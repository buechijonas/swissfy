import base64
import hmac
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings

PIN_VERIFIER_CONTEXT = b"swissfy-pin-verifier"


def _secret():
    return base64.b64decode(settings.CHAT_ENCRYPTION_KEY)


def _cipher():
    return AESGCM(_secret())


def _context(message):
    return f"{message.sender_id}:{message.recipient_id}".encode()


def wrap_message_key(message, message_key):
    nonce = os.urandom(12)
    return nonce + _cipher().encrypt(nonce, message_key, _context(message))


def unwrap_message_key(message):
    data = bytes(message.server_key)
    return _cipher().decrypt(data[:12], data[12:], _context(message))


def pin_verifier_digest(verifier):
    key = hmac.digest(_secret(), PIN_VERIFIER_CONTEXT, "sha256")
    return hmac.digest(key, verifier, "sha256").hex()


def pin_verifier_matches(digest, verifier):
    return hmac.compare_digest(digest, pin_verifier_digest(verifier))
