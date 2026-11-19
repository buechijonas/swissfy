from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from commons.serializers import BaseModelSerializer

from ..models import ContactGroup, SavedFolder
from .common import OwnedNameSerializerMixin

User = get_user_model()


class SavedFolderModelSerializer(BaseModelSerializer):
    class read(BaseModelSerializer.read):
        class Meta(BaseModelSerializer.read.Meta):
            model = SavedFolder
            fields = ["id", "name"]

    class write(OwnedNameSerializerMixin, BaseModelSerializer.write):
        class Meta(BaseModelSerializer.write.Meta):
            model = SavedFolder
            fields = ["name"]


class ContactGroupModelSerializer(BaseModelSerializer):
    class read(BaseModelSerializer.read):
        members = serializers.SlugRelatedField(slug_field="username", many=True, read_only=True)

        class Meta(BaseModelSerializer.read.Meta):
            model = ContactGroup
            fields = ["id", "name", "members"]

    class write(OwnedNameSerializerMixin, BaseModelSerializer.write):
        members = serializers.SlugRelatedField(
            slug_field="username",
            many=True,
            queryset=User.objects.filter(is_active=True),
            error_messages={"does_not_exist": _("The user “{value}” does not exist.")},
        )

        class Meta(BaseModelSerializer.write.Meta):
            model = ContactGroup
            fields = ["name", "members"]

        def validate_members(self, members):
            if self.context["request"].user in members:
                raise serializers.ValidationError(_("You cannot add yourself."))
            return members
