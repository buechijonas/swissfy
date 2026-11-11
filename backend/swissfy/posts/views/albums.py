from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from commons.views import BaseViewSet
from swissfy.social.users import can_view_profile

from ..models import Album, AlbumEntry, Post
from ..permissions import IsNotSuspended
from ..serializers import AlbumEntryModelSerializer, AlbumModelSerializer

User = get_user_model()


def apply_order(items, values, field):
    by_uuid = {item.uuid: item for item in items}
    try:
        uuids = [UUID(str(value)) for value in values]
    except (TypeError, ValueError):
        uuids = None
    if uuids is None or sorted(uuids) != sorted(by_uuid):
        raise ValidationError({field: ["Ungültige Reihenfolge."]})
    for position, value in enumerate(uuids):
        by_uuid[value].position = position
    return list(by_uuid.values())


class AlbumResponseMixin:
    def album_response(self, album, status_code=status.HTTP_200_OK):
        context = self.get_serializer_context()
        entries = album.entries.filter(
            post__in=Post.objects.apply_acl(self.request.user).values("pk")
        ).order_by(F("date").asc(nulls_last=True), "position", "id")
        data = {
            **AlbumModelSerializer.read(album, context=context).data,
            "owner": album.owner.username,
            "entries": AlbumEntryModelSerializer.read(
                entries.select_related("post__author__profile"), many=True, context=context
            ).data,
        }
        return Response(data, status=status_code)

    def own_album(self, uuid):
        return get_object_or_404(Album, uuid=uuid, owner=self.request.user)


class AlbumViewSet(AlbumResponseMixin, BaseViewSet):
    serializer_class = AlbumModelSerializer
    lookup_field = "uuid"
    permission_action_classes = {"create": [IsAuthenticated, IsNotSuspended]}

    def get_queryset(self):
        return Album.objects.select_related("owner__profile")

    def list(self, request, username):
        owner = get_object_or_404(User.objects.select_related("profile"), username=username)
        if not can_view_profile(request.user, owner):
            raise PermissionDenied("Diese Alben sind nicht sichtbar.")
        albums = owner.albums.select_related("cover__post")
        return Response(self.get_serializer(albums, many=True).data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            request.user.albums.update(position=F("position") + 1)
            album = serializer.save(owner=request.user, position=0)
        return self.album_response(album, status.HTTP_201_CREATED)

    def order(self, request):
        albums = apply_order(request.user.albums.all(), request.data.get("albums"), "albums")
        Album.objects.bulk_update(albums, ["position"])
        albums = request.user.albums.select_related("cover__post")
        return Response(
            AlbumModelSerializer.read(albums, many=True, context=self.get_serializer_context()).data
        )

    def retrieve(self, request, uuid):
        album = self.get_object()
        if not can_view_profile(request.user, album.owner):
            raise PermissionDenied("Dieses Album ist nicht sichtbar.")
        return self.album_response(album)

    def partial_update(self, request, uuid):
        serializer = self.get_serializer(self.own_album(uuid), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return self.album_response(serializer.save())

    def destroy(self, request, uuid):
        self.own_album(uuid).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AlbumEntryViewSet(AlbumResponseMixin, BaseViewSet):
    serializer_class = AlbumEntryModelSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return AlbumEntry.objects.select_related("album").filter(album__owner=self.request.user)

    def create(self, request, uuid):
        album = self.own_album(uuid)
        serializer = self.get_serializer(data=request.data.get("entries"), many=True)
        serializer.is_valid(raise_exception=True)
        posts = [entry["post"] for entry in serializer.validated_data]
        if len(set(posts)) != len(posts) or album.entries.filter(post__in=posts).exists():
            raise ValidationError({"entries": ["Ein Feed ist schon im Album."]})
        last = album.entries.order_by("-position").values_list("position", flat=True).first()
        start = 0 if last is None else last + 1
        AlbumEntry.objects.bulk_create(
            AlbumEntry(album=album, position=start + index, **entry)
            for index, entry in enumerate(serializer.validated_data)
        )
        return self.album_response(album, status.HTTP_201_CREATED)

    def partial_update(self, request, uuid):
        entry = self.get_object()
        serializer = self.get_serializer(entry, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if "post" in serializer.validated_data:
            raise ValidationError({"post": ["Der Feed eines Eintrags kann nicht geändert werden."]})
        serializer.save()
        return self.album_response(entry.album)

    def destroy(self, request, uuid):
        entry = self.get_object()
        entry.delete()
        entry.album.refresh_from_db()
        return self.album_response(entry.album)
