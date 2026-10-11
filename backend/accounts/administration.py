from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from main.pagination import NextPagePagination
from moderation.sanctions import role_locked_until

from .roles import USER_ORDERING, IsAdmin, Role, role_badge, role_of, set_role, with_role_rank

User = get_user_model()


class AdminUserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    role = serializers.ChoiceField(choices=Role.choices, source="current_role")
    badge = serializers.SerializerMethodField()
    role_locked_until = serializers.SerializerMethodField()
    is_self = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "avatar",
            "role",
            "badge",
            "role_locked_until",
            "is_self",
        ]
        read_only_fields = ["username", "first_name", "last_name"]

    def get_avatar(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.avatar if profile else ""

    def get_badge(self, obj):
        return role_badge(obj)

    def get_role_locked_until(self, obj):
        return role_locked_until(obj)

    def get_is_self(self, obj):
        return obj == self.context["request"].user

    def to_representation(self, obj):
        obj.current_role = role_of(obj)
        return super().to_representation(obj)

    def update(self, user, data):
        if user == self.context["request"].user:
            raise PermissionDenied("Du kannst deine eigene Rolle nicht ändern.")
        if role_locked_until(user):
            raise PermissionDenied(
                "Die Rolle ist gesperrt, bis alle Verwarnungen verjährt und Sperren abgelaufen sind."
            )
        set_role(user, data["current_role"])
        return User.objects.prefetch_related("groups").get(pk=user.pk)


class AdminRoleView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response([{"value": value, "label": label} for value, label in Role.choices])


class AdminUserListView(generics.ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = AdminUserSerializer
    pagination_class = NextPagePagination

    def get_queryset(self):
        users = User.objects.filter(is_active=True).select_related("profile")
        for term in self.request.query_params.get("q", "").split():
            users = users.filter(
                Q(username__icontains=term)
                | Q(first_name__icontains=term)
                | Q(last_name__icontains=term)
            )
        role = self.request.query_params.get("role")
        if role == Role.DEFAULT:
            users = users.filter(Q(groups__name=Role.DEFAULT.label) | Q(groups__isnull=True))
        elif role in Role.values:
            users = users.filter(groups__name=Role(role).label)
        return with_role_rank(users).prefetch_related("groups").order_by(*USER_ORDERING)


class AdminUserView(generics.UpdateAPIView):
    permission_classes = [IsAdmin]
    serializer_class = AdminUserSerializer
    lookup_field = "username"
    http_method_names = ["patch"]

    def get_object(self):
        return get_object_or_404(User, username=self.kwargs["username"], is_active=True)
