from uuid import uuid4

from django.db import models

from . import encryption


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


class EncryptedTextField(models.TextField):
    def context(self):
        return f"{self.model._meta.label}.{self.name}".encode()

    def from_db_value(self, value, expression, connection):
        return encryption.decrypt_text(value, self.context())

    def get_prep_value(self, value):
        return encryption.encrypt_text(super().get_prep_value(value), self.context())
