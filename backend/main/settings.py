"""
Django settings for main project.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/6.0/ref/settings/
"""

from pathlib import Path
import os

from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"

# SECURITY WARNING: keep the secret key used in production secret!
# The fallback below is committed to the repo, so it is public - fine for local
# dev, but refuse to start with it once DEBUG is off.
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY must be set in the environment when DJANGO_DEBUG=false."
        )
    SECRET_KEY = "django-insecure-swissfy-local-development-only-0c9f2e7a41b5d8"

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,backend").split(",")

CSRF_TRUSTED_ORIGINS = os.getenv(
    "DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:5175,http://127.0.0.1:5175"
).split(",")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5175")

# govex is the identity provider (OIDC). GOVEX_PUBLIC_URL is where the browser
# is sent to log in; GOVEX_INTERNAL_URL is where this backend reaches govex for
# the token/userinfo exchange. They only differ in local Docker dev, where
# "localhost" inside this container isn't the host. GOVEX_ACCOUNT_URL is where
# users change their password, username, email and profile.
GOVEX_PUBLIC_URL = os.getenv("GOVEX_PUBLIC_URL")
GOVEX_ACCOUNT_URL = os.getenv("GOVEX_ACCOUNT_URL")
GOVEX_INTERNAL_URL = os.getenv("GOVEX_INTERNAL_URL", GOVEX_PUBLIC_URL)
GOVEX_CLIENT_ID = os.getenv("GOVEX_CLIENT_ID")
GOVEX_CLIENT_SECRET = os.getenv("GOVEX_CLIENT_SECRET")
GOVEX_REDIRECT_URI = os.getenv("GOVEX_REDIRECT_URI")
if not DEBUG and not all(
    [
        GOVEX_PUBLIC_URL,
        GOVEX_ACCOUNT_URL,
        GOVEX_CLIENT_ID,
        GOVEX_CLIENT_SECRET,
        GOVEX_REDIRECT_URI,
    ]
):
    raise ImproperlyConfigured(
        "GOVEX_PUBLIC_URL, GOVEX_ACCOUNT_URL, GOVEX_CLIENT_ID, GOVEX_CLIENT_SECRET and "
        "GOVEX_REDIRECT_URI must be set in the environment when DJANGO_DEBUG=false."
    )

CHAT_ENCRYPTION_KEY = os.getenv("CHAT_ENCRYPTION_KEY")
if not CHAT_ENCRYPTION_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "CHAT_ENCRYPTION_KEY must be set in the environment when DJANGO_DEBUG=false."
        )
    CHAT_ENCRYPTION_KEY = "c3dpc3NmeS1sb2NhbC1jaGF0LWtleS1kZXYtb25seSE="

CHAT_RETENTION_DAYS = 14
CHAT_SLOW_MODE_SECONDS = 5

# Caddy terminates TLS and talks plain HTTP to this container, marking the
# original scheme in this header so Django knows the outer request was HTTPS.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# Cookies don't care about ports, so in local dev every app on localhost shares
# them. Own names keep a wintersehn login from overwriting the swissfy one.
SESSION_COOKIE_NAME = "swissfy_sessionid"
CSRF_COOKIE_NAME = "swissfy_csrftoken"


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "accounts",
    "social",
    "chats",
    "posts",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "main.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "main.wsgi.application"


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "swissfy"),
        "USER": os.getenv("DB_USER", "swissfy"),
        "PASSWORD": os.getenv("DB_PASSWORD", "swissfy"),
        "HOST": os.getenv("DB_HOST", "db"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {"options": "-c jit=off"},
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = "de-ch"

TIME_ZONE = "Europe/Zurich"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
