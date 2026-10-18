from django.contrib.auth.models import Group
from django.db import models
from django.db.models import (
    Case,
    IntegerField,
    OuterRef,
    Subquery,
    Value,
    When,
    prefetch_related_objects,
)
from django.db.models.functions import Coalesce
from rest_framework.permissions import BasePermission


class Role(models.TextChoices):
    DEFAULT = "default", "Standard"
    VERIFIED = "verified", "Verifiziert"
    SUPPORT = "support", "Support"
    MODERATOR = "moderator", "Moderator"
    ADMIN = "admin", "Admin"


ROLE_BY_GROUP = {role.label: role for role in Role}
ROLE_ORDER = [Role.ADMIN, Role.MODERATOR, Role.SUPPORT, Role.VERIFIED, Role.DEFAULT]
NAME_ORDERING = ["username", "first_name", "last_name"]
USER_ORDERING = ["role_rank", *NAME_ORDERING]
MODERATING_ROLES = {Role.MODERATOR, Role.ADMIN}


def with_role_rank(users):
    ranks = Case(
        *(When(name=role.label, then=Value(index)) for index, role in enumerate(ROLE_ORDER)),
        output_field=IntegerField(),
    )
    rank = Group.objects.filter(user=OuterRef("pk")).annotate(rank=ranks).values("rank")[:1]
    default = Value(ROLE_ORDER.index(Role.DEFAULT))
    return users.annotate(role_rank=Coalesce(Subquery(rank), default))


def role_of(user):
    if user.pk and "groups" not in getattr(user, "_prefetched_objects_cache", {}):
        prefetch_related_objects([user], "groups")
    group = next(iter(user.groups.all()), None)
    return ROLE_BY_GROUP.get(group.name, Role.DEFAULT) if group else Role.DEFAULT


def set_role(user, role):
    user.groups.set([Group.objects.get(name=Role(role).label)])


def role_badge(user):
    role = role_of(user)
    return None if role == Role.DEFAULT else {"key": role.value, "label": role.label}


def is_admin(user):
    return user.is_authenticated and role_of(user) == Role.ADMIN


def outranks(author, viewer):
    return is_admin(author) and not is_admin(viewer)


def is_moderator(user):
    return user.is_authenticated and role_of(user) in MODERATING_ROLES


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return is_admin(request.user)


class IsModerator(BasePermission):
    def has_permission(self, request, view):
        return is_moderator(request.user)
