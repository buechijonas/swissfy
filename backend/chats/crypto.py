import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings


def _cipher():
    return AESGCM(base64.b64decode(settings.CHAT_ENCRYPTION_KEY))


def _context(message):
    return f"{message.sender_id}:{message.recipient_id}".encode()


def wrap_message_key(message, message_key):
    nonce = os.urandom(12)
    return nonce + _cipher().encrypt(nonce, message_key, _context(message))


def unwrap_message_key(message):
    data = bytes(message.server_key)
    return _cipher().decrypt(data[:12], data[12:], _context(message))
