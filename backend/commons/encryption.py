import base64
import io
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings

TEXT_PREFIX = "enc:"
FILE_MAGIC = b"SWF1"
NONCE = 12
TAG = 16
KEY = 32
CHUNK = 64 * 1024
PREFIX = len(FILE_MAGIC) + 1
HEADER = PREFIX + NONCE + KEY + TAG


def keys():
    entries = (entry.split(":", 1) for entry in settings.CONTENT_ENCRYPTION_KEYS.split(","))
    return {int(key_id): base64.b64decode(key) for key_id, key in entries}


def current_key():
    return next(iter(keys().items()))


def encrypt_text(value, context):
    if value is None:
        return None
    key_id, key = current_key()
    nonce = os.urandom(NONCE)
    data = nonce + AESGCM(key).encrypt(nonce, value.encode(), context)
    return f"{TEXT_PREFIX}{key_id}:{base64.b64encode(data).decode()}"


def decrypt_text(value, context):
    if value is None or not value.startswith(TEXT_PREFIX):
        return value
    key_id, data = value.removeprefix(TEXT_PREFIX).split(":", 1)
    data = base64.b64decode(data)
    return AESGCM(keys()[int(key_id)]).decrypt(data[:NONCE], data[NONCE:], context).decode()


def chunk_nonce(index, last):
    return index.to_bytes(NONCE - 1, "big") + bytes([last])


def encrypt_file(source, target):
    key_id, master = current_key()
    file_key = AESGCM.generate_key(256)
    nonce = os.urandom(NONCE)
    header = FILE_MAGIC + bytes([key_id])
    target.write(header + nonce + AESGCM(master).encrypt(nonce, file_key, header))
    cipher = AESGCM(file_key)
    index, chunk = 0, read_chunk(source)
    while True:
        following = read_chunk(source)
        target.write(cipher.encrypt(chunk_nonce(index, not following), chunk, None))
        if not following:
            return
        index, chunk = index + 1, following


def read_chunk(source):
    data = b""
    while len(data) < CHUNK:
        part = source.read(CHUNK - len(data))
        if not part:
            break
        data += part
    return data


def plain_size(size):
    full, rest = divmod(size - HEADER, CHUNK + TAG)
    return full * CHUNK + max(rest - TAG, 0)


def is_encrypted(raw):
    encrypted = raw.read(len(FILE_MAGIC)) == FILE_MAGIC
    raw.seek(0)
    return encrypted


class DecryptedFile(io.RawIOBase):
    def __init__(self, raw, size):
        super().__init__()
        header = raw.read(HEADER)
        prefix, nonce, wrapped = header[:PREFIX], header[PREFIX:][:NONCE], header[PREFIX + NONCE :]
        self.cipher = AESGCM(AESGCM(keys()[prefix[-1]]).decrypt(nonce, wrapped, prefix))
        self.raw = raw
        self.size = plain_size(size)
        self.chunks = max(-(-(size - HEADER) // (CHUNK + TAG)), 1)
        self.position = 0
        self.cached = (None, b"")

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=io.SEEK_SET):
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self.position, io.SEEK_END: self.size}[whence]
        self.position = max(base + offset, 0)
        return self.position

    def readinto(self, buffer):
        filled = 0
        while filled < len(buffer) and self.position < self.size:
            index, skip = divmod(self.position, CHUNK)
            data = self.chunk(index)[skip : skip + len(buffer) - filled]
            buffer[filled : filled + len(data)] = data
            filled += len(data)
            self.position += len(data)
        return filled

    def chunk(self, index):
        if self.cached[0] != index:
            self.raw.seek(HEADER + index * (CHUNK + TAG))
            nonce = chunk_nonce(index, index == self.chunks - 1)
            self.cached = (index, self.cipher.decrypt(nonce, self.raw.read(CHUNK + TAG), None))
        return self.cached[1]

    def close(self):
        self.raw.close()
        super().close()
