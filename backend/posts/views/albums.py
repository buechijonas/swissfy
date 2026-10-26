from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from moderation.sanctions import ensure_not_suspended
from social.serializers import can_view_profile

from ..models import Album, AlbumEntry
from ..queries import visible_posts
from ..serializers import AlbumEntrySerializer, AlbumSerializer

User = get_user_model()


def viewable_album(request, uuid):
    album = get_object_or_404(Album.objects.select_related("owner__profile"), uuid=uuid)
    if not can_view_profile(request.user, album.owner):
        raise PermissionDenied("Dieses Album ist nicht sichtbar.")
    return album


def album_response(request, album, status_code=status.HTTP_200_OK):
    context = {"request": request}
    entries = album.entries.filter(post__in=visible_posts(request.user).values("pk")).order_by(
        F("date").asc(nulls_last=True), "position", "id"
    )
    data = {
        **AlbumSerializer(album, context=context).data,
        "owner": album.owner.username,
        "entries": AlbumEntrySerializer(
            entries.select_related("post__author__profile"), many=True, context=context
        ).data,
    }
    return Response(data, status=status_code)


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


class UserAlbumListView(APIView):
    def get(self, request, username):
        owner = get_object_or_404(User.objects.select_related("profile"), username=username)
        if not can_view_profile(request.user, owner):
            raise PermissionDenied("Diese Alben sind nicht sichtbar.")
        albums = owner.albums.select_related("cover__post")
        serializer = AlbumSerializer(albums, many=True, context={"request": request})
        return Response(serializer.data)


class AlbumListView(APIView):
    def post(self, request):
        ensure_not_suspended(request.user)
        serializer = AlbumSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            request.user.albums.update(position=F("position") + 1)
            album = serializer.save(owner=request.user, position=0)
        return album_response(request, album, status.HTTP_201_CREATED)


class AlbumOrderView(APIView):
    def put(self, request):
        albums = apply_order(request.user.albums.all(), request.data.get("albums"), "albums")
        Album.objects.bulk_update(albums, ["position"])
        serializer = AlbumSerializer(
            request.user.albums.select_related("cover__post"),
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class AlbumDetailView(APIView):
    def get(self, request, uuid):
        return album_response(request, viewable_album(request, uuid))

    def patch(self, request, uuid):
        album = get_object_or_404(Album, uuid=uuid, owner=request.user)
        serializer = AlbumSerializer(
            album, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        return album_response(request, serializer.save())

    def delete(self, request, uuid):
        get_object_or_404(Album, uuid=uuid, owner=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def own_album(request, uuid):
    return get_object_or_404(Album, uuid=uuid, owner=request.user)


class AlbumEntryListView(APIView):
    def post(self, request, uuid):
        album = own_album(request, uuid)
        serializer = AlbumEntrySerializer(
            data=request.data.get("entries"), many=True, context={"request": request}
        )
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
        return album_response(request, album, status.HTTP_201_CREATED)


class AlbumEntryDetailView(APIView):
    def get_entry(self, request, uuid):
        entries = AlbumEntry.objects.select_related("album")
        return get_object_or_404(entries, uuid=uuid, album__owner=request.user)

    def patch(self, request, uuid):
        entry = self.get_entry(request, uuid)
        serializer = AlbumEntrySerializer(
            entry, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        if "post" in serializer.validated_data:
            raise ValidationError({"post": ["Der Feed eines Eintrags kann nicht geändert werden."]})
        serializer.save()
        return album_response(request, entry.album)

    def delete(self, request, uuid):
        entry = self.get_entry(request, uuid)
        entry.delete()
        entry.album.refresh_from_db()
        return album_response(request, entry.album)
