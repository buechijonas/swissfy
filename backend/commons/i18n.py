from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext as _

FALLBACK_LANGUAGE = "en"


def localized(texts):
    return texts.get(get_language(), texts[FALLBACK_LANGUAGE])


def local_date(value):
    return timezone.localtime(value).strftime(_("%d/%m/%Y"))


def local_datetime(value):
    return timezone.localtime(value).strftime(_("%d/%m/%Y, %H:%M"))
