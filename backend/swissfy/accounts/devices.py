import hashlib
import secrets
from datetime import timedelta

from django.utils import timezone

from .models import DeviceToken

DEVICE_TOKEN_IDLE_DAYS = 365
SESSION_KEY = "device_token_id"


def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def find_device(token):
    if not isinstance(token, str) or not token:
        return None
    cutoff = timezone.now() - timedelta(days=DEVICE_TOKEN_IDLE_DAYS)
    return (
        DeviceToken.objects.select_related("user")
        .filter(token_hash=hash_token(token), last_used_at__gte=cutoff, user__is_active=True)
        .first()
    )


def remember_device(request, device):
    device.save(update_fields=["last_used_at"])
    request.session[SESSION_KEY] = device.pk


def keep_or_issue(request, token):
    device = find_device(token)
    if device is None or device.user_id != request.user.pk:
        cutoff = timezone.now() - timedelta(days=DEVICE_TOKEN_IDLE_DAYS)
        DeviceToken.objects.filter(user=request.user, last_used_at__lt=cutoff).delete()
        token = secrets.token_urlsafe(32)
        device = DeviceToken.objects.create(user=request.user, token_hash=hash_token(token))
    remember_device(request, device)
    return token


def forget_device(request):
    device_id = request.session.pop(SESSION_KEY, None)
    if device_id is not None:
        DeviceToken.objects.filter(pk=device_id, user=request.user).delete()
