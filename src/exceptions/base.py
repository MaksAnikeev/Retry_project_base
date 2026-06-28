import http


class BaseDomainException(Exception):
    http_status_code: int = http.HTTPStatus.INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None):
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)