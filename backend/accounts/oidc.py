import base64
import hashlib
import hmac
import json
import logging
import secrets
import time
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import AVATAR_CHOICES, DEFAULT_ROLE, UserProfile, get_or_create_profile

User = get_user_model()

logger = logging.getLogger(__name__)

SCOPE = "openid profile email govex_meta"

MAX_CLOCK_SKEW_SECONDS = 300


def code_challenge(verifier):
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def redirect_to_frontend(path):
    return HttpResponseRedirect(f"{settings.FRONTEND_URL}{path}")


def govex_login(request):
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)
    request.session["govex_oauth_state"] = state
    request.session["govex_oauth_code_verifier"] = code_verifier

    params = {
        "response_type": "code",
        "client_id": settings.GOVEX_CLIENT_ID,
        "redirect_uri": settings.GOVEX_REDIRECT_URI,
        "scope": SCOPE,
        "state": state,
        "code_challenge": code_challenge(code_verifier),
        "code_challenge_method": "S256",
    }
    return HttpResponseRedirect(
        f"{settings.GOVEX_PUBLIC_URL}/application/o/authorize/?{urlencode(params)}"
    )


def govex_account(request):
    return HttpResponseRedirect(settings.GOVEX_ACCOUNT_URL)


def fetch_userinfo(code, code_verifier):
    token_response = requests.post(
        f"{settings.GOVEX_INTERNAL_URL}/application/o/token/",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.GOVEX_REDIRECT_URI,
            "client_id": settings.GOVEX_CLIENT_ID,
            "client_secret": settings.GOVEX_CLIENT_SECRET,
            "code_verifier": code_verifier,
        },
        timeout=10,
    )
    if not token_response.ok:
        logger.warning(
            "govex token exchange failed (%s): %s",
            token_response.status_code,
            token_response.text[:500],
        )
        return None

    userinfo_response = requests.get(
        f"{settings.GOVEX_INTERNAL_URL}/application/o/userinfo/",
        headers={"Authorization": f"Bearer {token_response.json()['access_token']}"},
        timeout=10,
    )
    if not userinfo_response.ok:
        logger.warning(
            "govex userinfo request failed (%s): %s",
            userinfo_response.status_code,
            userinfo_response.text[:500],
        )
        return None
    return userinfo_response.json()


def create_user(govex_sub, username, email):
    with transaction.atomic():
        release_username(username)
        user = User(username=username, email=email)
        user.set_unusable_password()
        user.save()
        UserProfile.objects.create(user=user, govex_sub=govex_sub)
        user.groups.add(Group.objects.get(name=DEFAULT_ROLE))
    return user


def claimable_username(username, govex_sub, owner=None):
    staff = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True), username=username)
    if staff.exclude(pk=getattr(owner, "pk", None)).exists():
        return f"govex-{govex_sub[:8]}"
    return username


def release_username(username, owner=None):
    holder = User.objects.filter(username=username).exclude(pk=getattr(owner, "pk", None)).first()
    if holder is not None:
        holder.username = f"{holder.username[:140]}-{holder.pk}"
        holder.save(update_fields=["username"])


def find_profile(govex_sub):
    if not isinstance(govex_sub, str) or not govex_sub:
        return None
    return UserProfile.objects.filter(govex_sub=govex_sub).select_related("user").first()


def sync_user(user, username, email):
    if user.username == username and user.email == email:
        return
    with transaction.atomic():
        if user.username != username:
            release_username(username, owner=user)
        user.username, user.email = username, email
        user.save(update_fields=["username", "email"])


def sync_meta(user, meta):
    if meta is None:
        return
    profile = get_or_create_profile(user)
    user.first_name = (meta.get("first_name") or "")[:150]
    user.last_name = (meta.get("last_name") or "")[:150]
    user.save(update_fields=["first_name", "last_name"])
    profile.birthdate = parse_date(meta.get("birthdate") or "")
    avatar = meta.get("avatar") or ""
    profile.avatar = avatar if avatar in AVATAR_CHOICES else ""
    profile.save(update_fields=["birthdate", "avatar"])


def govex_callback(request):
    expected_state = request.session.pop("govex_oauth_state", None)
    code_verifier = request.session.pop("govex_oauth_code_verifier", None)
    code = request.GET.get("code")
    if not code or not expected_state or request.GET.get("state") != expected_state:
        if request.user.is_authenticated:
            return redirect_to_frontend("/")
        logger.warning(
            "govex callback rejected: code=%s, session state=%s, error=%s",
            bool(code),
            bool(expected_state),
            request.GET.get("error"),
        )
        return redirect_to_frontend("/login?error=oidc_failed")

    userinfo = fetch_userinfo(code, code_verifier)
    if userinfo is None:
        return redirect_to_frontend("/login?error=oidc_failed")

    govex_sub = str(userinfo["sub"])
    email = userinfo.get("email", "")
    username = userinfo.get("preferred_username") or f"govex-{govex_sub[:8]}"

    profile = find_profile(govex_sub)
    if profile is None:
        user = create_user(govex_sub, claimable_username(username, govex_sub), email)
    else:
        user = profile.user
        sync_user(user, claimable_username(username, govex_sub, owner=user), email)
    sync_meta(user, userinfo.get("meta"))

    login(request, user)
    return redirect_to_frontend("/")


def valid_govex_signature(request):
    timestamp = request.headers.get("X-Govex-Timestamp", "")
    signature = request.headers.get("X-Govex-Signature", "")
    if not settings.GOVEX_CLIENT_SECRET:
        return False
    if not timestamp.isdigit() or abs(time.time() - int(timestamp)) > MAX_CLOCK_SKEW_SECONDS:
        return False
    expected = hmac.new(
        settings.GOVEX_CLIENT_SECRET.encode(),
        f"{timestamp}.".encode() + request.body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@csrf_exempt
@require_POST
def govex_account_deleted(request):
    if not valid_govex_signature(request):
        return HttpResponse(status=403)
    try:
        payload = json.loads(request.body)
    except ValueError:
        return HttpResponse(status=400)

    profile = find_profile(payload.get("sub"))
    if profile is not None:
        profile.user.delete()
    return HttpResponse(status=204)


@csrf_exempt
@require_POST
def govex_account_updated(request):
    if not valid_govex_signature(request):
        return HttpResponse(status=403)
    try:
        payload = json.loads(request.body)
    except ValueError:
        return HttpResponse(status=400)

    profile = find_profile(payload.get("sub"))
    if profile is not None and payload.get("username"):
        username = claimable_username(payload["username"], profile.govex_sub, owner=profile.user)
        sync_user(profile.user, username, payload.get("email") or "")
    if profile is not None:
        sync_meta(profile.user, payload.get("meta"))
    return HttpResponse(status=204)
