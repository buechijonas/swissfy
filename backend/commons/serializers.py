from rest_framework import serializers

READ_ACTIONS = {"list", "retrieve"}


class BaseModelSerializer:
    class read(serializers.ModelSerializer):
        class Meta:
            fields = []

    class write(serializers.ModelSerializer):
        class Meta:
            fields = []

    @classmethod
    def for_action(cls, action):
        return cls.read if action in READ_ACTIONS else cls.write


class UUIDModelSerializer(BaseModelSerializer):
    class read(BaseModelSerializer.read):
        id = serializers.UUIDField(source="uuid", read_only=True)

        class Meta(BaseModelSerializer.read.Meta):
            fields = ["id"]
