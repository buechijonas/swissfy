from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param

MAX_PAGE = 100_000


class NextPagePagination(PageNumberPagination):
    page_size = 20

    def paginate_queryset(self, queryset, request, view=None):
        self.request = request
        try:
            self.number = max(1, int(request.query_params.get(self.page_query_param, 1)))
        except ValueError:
            raise NotFound("Ungültige Seite.")
        if self.number > MAX_PAGE:
            raise NotFound("Ungültige Seite.")
        start = (self.number - 1) * self.page_size
        items = list(queryset[start : start + self.page_size + 1])
        self.has_next = len(items) > self.page_size
        return items[: self.page_size]

    def get_paginated_response(self, data):
        next_url = None
        if self.has_next:
            next_url = replace_query_param(
                self.request.get_full_path(), self.page_query_param, self.number + 1
            )
        return Response({"next": next_url, "results": data})
