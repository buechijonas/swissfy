import base64
import binascii

from rest_framework import serializers

from commons.serializers import BaseModelSerializer
from swissfy.accounts.models import UserProfile
from swissfy.social.serializers import ProfileModelSerializer

from .models import ChatKey, Message

Protection = UserProfile.ChatProtection

BASE64 = r"^[A-Za-z0-9+/]*={0,2}$"
P256_COORDINATE = r"^[A-Za-z0-9_-]{43}$"


def base64_field(max_length, **kwargs):
    return serializers.RegexField(BASE64, max_length=max_length, **kwargs)


class EcdhKeySerializer(serializers.Serializer):
    kty = serializers.ChoiceField(["EC"])
    crv = serializers.ChoiceField(["P-256"])
    x = serializers.RegexField(P256_COORDINATE)
    y = serializers.RegexField(P256_COORDINATE)


class PublicKeySerializer(serializers.Serializer):
    ecdh = EcdhKeySerializer()
    kem = base64_field(2000)


class ChatKeyModelSerializer(BaseModelSerializer):
    class read(BaseModelSerializer.read):
        class Meta(BaseModelSerializer.read.Meta):
            model = ChatKey
            fields = ["id", "kind", "public_key"]

    class pin(read):
        class Meta(BaseModelSerializer.read.Meta):
            model = ChatKey
            fields = ["id", "kind", "public_key", "wrapped_private_key", "salt", "iv"]

    class write(serializers.Serializer):
        public_key = PublicKeySerializer()
        wrapped_private_key = base64_field(10000, required=False)
        salt = base64_field(64, required=False)
        iv = base64_field(32, required=False)

    class device(serializers.Serializer):
        public_key = PublicKeySerializer()


class ProtectionSerializer:
    class read(serializers.Serializer):
        mode = serializers.CharField(read_only=True)
        keys = ChatKeyModelSerializer.read(many=True, read_only=True)
        pin_key = ChatKeyModelSerializer.pin(read_only=True, allow_null=True)

    class write(serializers.Serializer):
        mode = serializers.ChoiceField(Protection.choices)
        key = ChatKeyModelSerializer.write(required=False)

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


class EnvelopeSerializer(serializers.Serializer):
    key = serializers.IntegerField()
    kem = base64_field(2000)
    ecdh = EcdhKeySerializer()
    wrapped = base64_field(100)
    iv = base64_field(32)


class MessageModelSerializer(BaseModelSerializer):
    class read(BaseModelSerializer.read):
        sender = serializers.CharField(source="sender.username", read_only=True)
        envelopes = serializers.JSONField(source="envelope_data", read_only=True)
        message_key = serializers.CharField(read_only=True, allow_null=True)
        status = serializers.CharField(read_only=True, allow_null=True)
        is_own = serializers.BooleanField(read_only=True)

        class Meta(BaseModelSerializer.read.Meta):
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
                "is_own",
            ]

    class write(serializers.Serializer):
        ciphertext = base64_field(20000)
        iv = base64_field(32)
        envelopes = EnvelopeSerializer(many=True)
        message_key = base64_field(64, required=False)

        def validate_message_key(self, value):
            try:
                key = base64.b64decode(value, validate=True)
            except binascii.Error:
                key = b""
            if len(key) != 32:
                raise serializers.ValidationError("Ungültiger Schlüssel.")
            return key

    class query(serializers.Serializer):
        after = serializers.IntegerField(required=False)

    class receipt(serializers.Serializer):
        read = serializers.BooleanField(default=False)


class ConversationSerializer(ProfileModelSerializer.list):
    last_message = serializers.SerializerMethodField()
    unread = serializers.BooleanField(read_only=True)
    archived = serializers.BooleanField(read_only=True)
    pending = serializers.BooleanField(read_only=True)

    class Meta(ProfileModelSerializer.list.Meta):
        fields = [
            *ProfileModelSerializer.list.Meta.fields,
            "last_message",
            "unread",
            "archived",
            "pending",
        ]

    def message_of(self, partner):
        return self.context["messages"].get(partner.last_message_id)

    def get_last_message(self, partner):
        message = self.message_of(partner)
        if message is None:
            return None
        return MessageModelSerializer.read(message).data
