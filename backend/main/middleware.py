from django.http import HttpResponseBadRequest


class RejectNullBytes:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        values = [request.path, *request.GET.keys()]
        values += [value for _, items in request.GET.lists() for value in items]
        if any("\x00" in value for value in values):
            return HttpResponseBadRequest()
        return self.get_response(request)
