from rest_framework import serializers

from main.numbers import compact_number


class CompactNumberField(serializers.IntegerField):
    def __init__(self, **kwargs):
        super().__init__(read_only=True, **kwargs)

    def to_representation(self, value):
        return compact_number(value)


class ConstantField(serializers.Field):
    def __init__(self, value, **kwargs):
        super().__init__(source="*", read_only=True, **kwargs)
        self.value = value

    def to_representation(self, instance):
        return self.value
