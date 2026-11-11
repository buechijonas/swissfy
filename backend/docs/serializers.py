from rest_framework import serializers


class ChangelogSerializer(serializers.Serializer):
    version = serializers.CharField(read_only=True)
    bump = serializers.CharField(read_only=True)
    date = serializers.DateField(read_only=True)
    html = serializers.CharField(read_only=True)
