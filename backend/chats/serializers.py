import base64
import binascii

from rest_framework import serializers

from accounts.models import UserProfile

from .crypto import unwrap_message_key
from .models import ChatKey, Message

Protection = UserProfile.ChatProtection

BASE64 = r"^[A-Za-z0-9+/]*={0,2}$"


def base64_field(max_length, **kwargs):
    return serializers.RegexField(BASE64, max_length=max_length, **kwargs)


class EcdhKeyField(serializers.JSONField):
    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        if not (
            isinstance(data, dict)
            and data.get("kty") == "EC"
            and data.get("crv") == "P-256"
            and isinstance(data.get("x"), str)
            and isinstance(data.get("y"), str)
        ):
            raise serializers.ValidationError("Ungültiger Schlüssel.")
        return {key: data[key] for key in ["kty", "crv", "x", "y"]}


class PublicKeySerializer(serializers.Serializer):
    ecdh = EcdhKeyField()
    kem = base64_field(2000)


class ChatKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatKey
        fields = ["id", "kind", "public_key"]


class PinKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatKey
        fields = ["id", "kind", "public_key", "wrapped_private_key", "salt", "iv"]


class NewKeySerializer(serializers.Serializer):
    public_key = PublicKeySerializer()
    wrapped_private_key = base64_field(10000, required=False)
    salt = base64_field(64, required=False)
    iv = base64_field(32, required=False)


class DeviceKeyInputSerializer(serializers.Serializer):
    public_key = PublicKeySerializer()


class ProtectionInputSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(Protection.choices)
    key = NewKeySerializer(required=False)

    def validate(self, data):
        key = data.get("key")
        if data["mode"] == Protection.STANDARD:
            if key:
                raise serializers.ValidationError("Standard braucht keinen Schlüssel.")
        elif not key:
            raise serializers.ValidationError("Schlüssel fehlt.")
        elif data["mode"] == Protection.PIN and not all(
            key.get(field) for field in ["wrapped_private_key", "salt", "iv"]
        ):
            raise serializers.ValidationError("Der PIN-Schlüssel ist unvollständig.")
        return data


class EnvelopeInputSerializer(serializers.Serializer):
    key = serializers.IntegerField()
    kem = base64_field(2000)
    ecdh = EcdhKeyField()
    wrapped = base64_field(100)
    iv = base64_field(32)


class MessageInputSerializer(serializers.Serializer):
    ciphertext = base64_field(20000)
    iv = base64_field(32)
    envelopes = EnvelopeInputSerializer(many=True)
    message_key = base64_field(64, required=False)

    def validate_message_key(self, value):
        try:
            key = base64.b64decode(value, validate=True)
        except binascii.Error:
            key = b""
        if len(key) != 32:
            raise serializers.ValidationError("Ungültiger Schlüssel.")
        return key


class MessageQuerySerializer(serializers.Serializer):
    after = serializers.IntegerField(required=False)
    read = serializers.BooleanField(default=False)


def message_status(message, show_read):
    if message.read_at and show_read:
        return "read"
    if message.delivered_at:
        return "delivered"
    return "sent"


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source="sender.username")
    envelopes = serializers.SerializerMethodField()
    message_key = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "created_at",
            "ciphertext",
            "iv",
            "envelopes",
            "message_key",
            "status",
        ]

    def get_status(self, obj):
        if obj.sender_id != self.context["viewer"].pk:
            return None
        return message_status(obj, self.context["show_read"])

    def get_envelopes(self, obj):
        return [{"key": e.key_id, **e.data} for e in obj.envelopes.all()]

    def get_message_key(self, obj):
        if obj.server_key is None:
            return None
        return base64.b64encode(unwrap_message_key(obj)).decode()
