import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"

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

GOVEX_PUBLIC_URL = os.getenv("GOVEX_PUBLIC_URL")
GOVEX_ACCOUNT_URL = os.getenv("GOVEX_ACCOUNT_URL")
GOVEX_INTERNAL_URL = os.getenv("GOVEX_INTERNAL_URL", GOVEX_PUBLIC_URL)
GOVEX_CLIENT_ID = os.getenv("GOVEX_CLIENT_ID")
GOVEX_CLIENT_SECRET = os.getenv("GOVEX_CLIENT_SECRET")
GOVEX_REDIRECT_URI = os.getenv("GOVEX_REDIRECT_URI")

MONOLITH_API_TOKEN = os.getenv("MONOLITH_API_TOKEN")
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

CONSENT_PRIVATE_KEY = os.getenv("CONSENT_PRIVATE_KEY", "").replace("\\n", "\n")
if not DEBUG and not CONSENT_PRIVATE_KEY:
    raise ImproperlyConfigured(
        "CONSENT_PRIVATE_KEY must be set in the environment when DJANGO_DEBUG=false."
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

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

SESSION_COOKIE_NAME = "swissfy_sessionid"
CSRF_COOKIE_NAME = "swissfy_csrftoken"


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
    "moderation",
    "notifications",
    "achievements",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "main.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "main.middleware.RejectNullBytes",
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


LANGUAGE_CODE = "de-ch"

TIME_ZONE = "Europe/Zurich"

USE_I18N = True

USE_TZ = True


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
