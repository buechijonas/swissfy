from rest_framework import serializers

from .models import user_consent
from .roles import Role, role_badge, role_of


class RoleBadgeField(serializers.Field):
    def __init__(self, **kwargs):
        super().__init__(source="*", read_only=True, **kwargs)

    def to_representation(self, user):
        return role_badge(user)


class RoleField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        super().__init__(choices=Role.choices, source="*", **kwargs)

    def to_representation(self, user):
        return role_of(user).value

    def to_internal_value(self, data):
        return {"role": super().to_internal_value(data)}


class DisplayNameField(serializers.Field):
    def __init__(self, **kwargs):
        super().__init__(source="*", read_only=True, **kwargs)

    def to_representation(self, user):
        return user.get_full_name() or user.username


class ConsentField(serializers.Field):
    def __init__(self, **kwargs):
        super().__init__(source="*", read_only=True, **kwargs)

    def to_representation(self, user):
        return user_consent(user).status
