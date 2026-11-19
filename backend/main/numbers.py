from django.utils.formats import number_format
from django.utils.translation import gettext as _


def compact_number(value):
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value < 10_000:
        return f"{sign}{value}"
    if value < 1_000_000:
        return _("%(sign)s%(count)sK") % {"sign": sign, "count": value // 1000}
    tenths = value // 100_000
    millions = number_format(tenths // 10 if tenths % 10 == 0 else tenths / 10)
    return _("%(sign)s%(count)sM") % {"sign": sign, "count": millions}
