from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from commons.serializers import BaseModelSerializer, UUIDModelSerializer
from swissfy.accounts.roles import is_admin, role_badge
from swissfy.moderation.models import Suspension
from swissfy.social.pictures import PictureField

from .. import hashtags
from ..models import ContactGroup, Post

User = get_user_model()


class HashtagTextField(serializers.Field):
    def __init__(self, **kwargs):
        super().__init__(source="text", read_only=True, **kwargs)

    def to_representation(self, text):
        return hashtags.split(text)


class AuthorModelSerializer(BaseModelSerializer):
    class read(BaseModelSerializer.read):
        display_name = serializers.CharField(read_only=True)
        avatar = serializers.CharField(source="profile.avatar", read_only=True)
        picture = PictureField()
        role = serializers.SerializerMethodField()
        has_story = serializers.BooleanField(read_only=True)
        story_seen = serializers.BooleanField(read_only=True)

        class Meta(BaseModelSerializer.read.Meta):
            model = User
            fields = [
                "username",
                "display_name",
                "first_name",
                "last_name",
                "avatar",
                "picture",
                "role",
                "has_story",
                "story_seen",
            ]

        def get_role(self, obj):
            return role_badge(obj) if obj.viewer_can_view else None


class ModeratedSerializerMixin(serializers.Serializer):
    hidden = serializers.BooleanField(source="is_hidden", read_only=True)
    reported = serializers.BooleanField(read_only=True)
    can_report = serializers.BooleanField(read_only=True)
    moderated_actions = ["can_report"]

    def to_representation(self, obj):
        data = super().to_representation(obj)
        if self.context.get("moderation", False):
            for moderated_action in self.moderated_actions:
                data[moderated_action] = False
        return data


class UnavailableSerializer(UUIDModelSerializer.read):
    blocked = None
    hidden = None
    unavailable = serializers.SerializerMethodField()

    class Meta(UUIDModelSerializer.read.Meta):
        fields = UUIDModelSerializer.read.Meta.fields + ["unavailable"]

    def get_unavailable(self, obj):
        if obj.is_hidden:
            return self.blocked
        if Suspension.objects.running().filter(user=obj.author_id).exists():
            return _("This user has been suspended and is not visible.")
        return self.hidden


class AudienceSerializerMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["groups"].child_relation.queryset = ContactGroup.objects.filter(
            owner=self.context["request"].user
        )

    def clean_audience(self, data):
        if data.get("visibility") == Post.Visibility.GLOBAL and not is_admin(
            self.context["request"].user
        ):
            raise serializers.ValidationError({"visibility": _("Only admins can post globally.")})
        if data.get("visibility") == Post.Visibility.GROUPS:
            if not data.get("groups"):
                raise serializers.ValidationError({"groups": _("Choose at least one group.")})
        else:
            data["groups"] = []
        return data


class OwnedNameSerializerMixin:
    def validate_name(self, name):
        name = name.strip()
        owned = self.Meta.model.objects.filter(owner=self.context["request"].user, name=name)
        if self.instance:
            owned = owned.exclude(pk=self.instance.pk)
        if owned.exists():
            raise serializers.ValidationError(_("This name is already taken."))
        return name
