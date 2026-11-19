from django.utils.translation import gettext_lazy as _
from rest_framework import parsers
from rest_framework.exceptions import ParseError


class JSONParser(parsers.JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        try:
            return super().parse(stream, media_type, parser_context)
        except RecursionError:
            raise ParseError(_("The JSON is nested too deeply.")) from None
