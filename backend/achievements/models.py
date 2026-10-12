from django.conf import settings
from django.db import models


class Unlock(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="achievement_unlocks"
    )
    key = models.CharField(max_length=50)
    unlocked_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "key"], name="unique_achievement_unlock"),
        ]

    def __str__(self):
        return f"Unlock({self.user}, {self.key})"
