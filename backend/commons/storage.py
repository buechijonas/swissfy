import tempfile

from django.core.files import File
from django.core.files.storage import FileSystemStorage

from . import encryption


class EncryptedFileSystemStorage(FileSystemStorage):
    def _save(self, name, content):
        content.seek(0)
        with tempfile.TemporaryFile() as encrypted:
            encryption.encrypt_file(content, encrypted)
            return super()._save(name, File(encrypted))

    def _open(self, name, mode="rb"):
        file = super()._open(name, mode)
        if not encryption.is_encrypted(file):
            return file
        return File(encryption.DecryptedFile(file.file, super().size(name)), name)

    def size(self, name):
        with super()._open(name) as file:
            encrypted = encryption.is_encrypted(file)
        size = super().size(name)
        return encryption.plain_size(size) if encrypted else size
