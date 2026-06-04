

class BaseDomainException(Exception):
    http_status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None, error_code: str | None = None):
        self.detail = detail or self.detail
        self.error_code = error_code or self.error_code
        super().__init__(self.detail)