from django.conf import settings
from django.db import models

from commons.models import BaseModel

from .audience import NAME_LENGTH


class SavedFolder(BaseModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_folders"
    )
    name = models.CharField(max_length=NAME_LENGTH)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "name"], name="unique_saved_folder"),
        ]

    def __str__(self):
        return f"{self.owner}: {self.name}"


class SavedPost(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_posts"
    )
    post = models.ForeignKey("posts.Post", on_delete=models.CASCADE, related_name="saves")
    folder = models.ForeignKey(
        SavedFolder, on_delete=models.SET_NULL, null=True, blank=True, related_name="saved_posts"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "post"], name="unique_saved_post"),
        ]
