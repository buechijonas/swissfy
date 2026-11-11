from rest_framework import serializers

from main.numbers import compact_number


class CompactNumberField(serializers.IntegerField):
    def __init__(self, **kwargs):
        super().__init__(read_only=True, **kwargs)

    def to_representation(self, value):
        return compact_number(value)


class StrictCharField(serializers.CharField):
    def to_internal_value(self, data):
        if type(data) is not str:
            self.fail("invalid")
        return super().to_internal_value(data)
