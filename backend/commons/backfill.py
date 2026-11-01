import os
import tempfile
from pathlib import Path

from django.core.files.storage import default_storage

from .encryption import CHUNK, DecryptedFile, encrypt_file, is_encrypted


class BackfillError(Exception):
    pass


def chunks(file):
    return iter(lambda: file.read(CHUNK), b"")


def encrypt_stored(name):
    path = Path(default_storage.path(name))
    if not path.exists():
        return
    with path.open("rb") as source:
        if is_encrypted(source):
            return
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as target:
            encrypt_file(source, target)
    encrypted = Path(target.name)
    with path.open("rb") as original:
        decrypted = DecryptedFile(encrypted.open("rb"), encrypted.stat().st_size)
        with decrypted:
            same = decrypted.size == path.stat().st_size and all(
                a == b for a, b in zip(chunks(original), chunks(decrypted))
            )
    if not same:
        encrypted.unlink()
        raise BackfillError(f"{name} could not be encrypted.")
    os.replace(encrypted, path)


def encrypt_rows(model, texts=(), files=()):
    for row in model.objects.values("pk", *texts, *files).iterator():
        values = {field: row[field] for field in texts}
        if values:
            model.objects.filter(pk=row["pk"]).update(**values)
            if model.objects.values(*texts).get(pk=row["pk"]) != values:
                raise BackfillError(f"{model._meta.label} {row['pk']} could not be encrypted.")
        for field in files:
            if row[field]:
                encrypt_stored(row[field])
