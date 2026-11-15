from django.conf import settings
from django.db import models
from django.db.models import Exists, OuterRef, Q

from commons.models import BaseQuerySet, UUIDModel, boolean

from .audience import NAME_LENGTH
from .posts import Post


class AlbumQuerySet(BaseQuerySet):
    def with_details(self, viewer):
        cover = Post.objects.apply_acl(viewer).filter(pk=OuterRef("cover__post"))
        return self.select_related("owner", "cover__post").annotate(
            cover_visible=Exists(cover),
            is_own=boolean(Q(owner=viewer.pk)),
        )


class Album(UUIDModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="albums"
    )
    name = models.CharField(max_length=NAME_LENGTH)
    cover = models.ForeignKey(
        "AlbumEntry", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AlbumQuerySet.as_manager()

    class Meta:
        ordering = ["position", "-created_at", "-id"]

    def __str__(self):
        return self.name

    @property
    def cover_url(self):
        return self.cover.post.thumbnail_url if self.cover_visible else None

    @property
    def cover_entry(self):
        return self.cover.uuid if self.cover_visible else None


class AlbumEntry(UUIDModel):
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="entries")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="+")
    date = models.DateField(null=True, blank=True)
    title = models.CharField(max_length=NAME_LENGTH, blank=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(fields=["album", "post"], name="unique_album_post"),
        ]
