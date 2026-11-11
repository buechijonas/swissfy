from rest_framework import status
from rest_framework.exceptions import APIException


class BadRequest(APIException):
    status_code = status.HTTP_400_BAD_REQUEST


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT


class RetryLater(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS

    def __init__(self, detail, wait):
        super().__init__(detail)
        self.detail = {"detail": self.detail, "retry_after": wait}
        self.wait = wait
