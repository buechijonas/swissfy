from uuid import uuid4

from django.db import models


class BaseQuerySet(models.QuerySet):
    def apply_acl(self, user):
        return self.none()


class BaseModel(models.Model):
    objects = BaseQuerySet.as_manager()

    class Meta:
        abstract = True


class UUIDModel(BaseModel):
    uuid = models.UUIDField(default=uuid4, unique=True, editable=False)

    class Meta(BaseModel.Meta):
        abstract = True
