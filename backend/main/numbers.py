from django.utils.translation import gettext as _


def compact_number(value):
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value < 10_000:
        return f"{sign}{value}"
    if value < 1_000_000:
        return _("%(sign)s%(count)s Tsd.") % {"sign": sign, "count": value // 1000}
    millions = value // 100_000 / 10
    return f"{sign}{millions:g}M"
