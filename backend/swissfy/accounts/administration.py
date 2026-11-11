from django.contrib.auth import get_user_model
from django.db.models import BooleanField, ExpressionWrapper, Q
from rest_framework import mixins, serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from commons.serializers import BaseModelSerializer
from commons.views import BaseViewSet
from main.pagination import NextPagePagination
from swissfy.moderation.sanctions import annotate_role_lock, role_lock, role_locked_until
from swissfy.social.pictures import PictureField

from .fields import RoleBadgeField, RoleField
from .roles import USER_ORDERING, IsAdmin, Role, set_role, with_role_rank

User = get_user_model()


class RoleLockField(serializers.Field):
    def __init__(self, **kwargs):
        super().__init__(source="*", read_only=True, **kwargs)

    def to_representation(self, user):
        return role_lock(user)


class AdminUserModelSerializer(BaseModelSerializer):
    class read(BaseModelSerializer.read):
        avatar = serializers.CharField(source="profile.avatar", read_only=True)
        picture = PictureField()
        role = RoleField(read_only=True)
        badge = RoleBadgeField()
        role_locked_until = RoleLockField()
        is_self = serializers.BooleanField(read_only=True)

        class Meta(BaseModelSerializer.read.Meta):
            model = User
            fields = [
                "username",
                "first_name",
                "last_name",
                "avatar",
                "picture",
                "role",
                "badge",
                "role_locked_until",
                "is_self",
            ]

    class write(BaseModelSerializer.write):
        role = RoleField()

        class Meta(BaseModelSerializer.write.Meta):
            model = User
            fields = ["role"]

        def validate(self, data):
            if self.instance == self.context["request"].user:
                raise PermissionDenied("Du kannst deine eigene Rolle nicht ändern.")
            if role_locked_until(self.instance):
                raise PermissionDenied(
                    "Die Rolle ist gesperrt, bis alle Verwarnungen verjährt "
                    "und Sperren abgelaufen sind."
                )
            return data

        def update(self, user, data):
            set_role(user, data["role"])
            return user


def matching(users, query):
    for term in query.split():
        users = users.filter(
            Q(username__icontains=term)
            | Q(first_name__icontains=term)
            | Q(last_name__icontains=term)
        )
    return users


def with_role(users, role):
    if role == Role.DEFAULT:
        return users.filter(Q(groups__name=Role.DEFAULT.label) | Q(groups__isnull=True))
    if role in Role.values:
        return users.filter(groups__name=Role(role).label)
    return users


class AdminUserViewSet(BaseViewSet, mixins.ListModelMixin):
    permission_classes = [IsAdmin]
    serializer_class = AdminUserModelSerializer
    pagination_class = NextPagePagination
    lookup_field = "username"

    def get_queryset(self):
        is_self = ExpressionWrapper(Q(pk=self.request.user.pk), output_field=BooleanField())
        users = (
            User.objects.filter(is_active=True)
            .select_related("profile")
            .prefetch_related("groups")
            .annotate(is_self=is_self)
        )
        return annotate_role_lock(users)

    def filter_queryset(self, users):
        params = self.request.query_params
        users = with_role(matching(users, params.get("q", "")), params.get("role"))
        return with_role_rank(users).order_by(*USER_ORDERING)

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.respond(serializer.save())


class RoleViewSet(BaseViewSet):
    permission_classes = [IsAdmin]

    def list(self, request):
        return Response([{"value": value, "label": label} for value, label in Role.choices])
