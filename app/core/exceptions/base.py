class AppException(Exception):
    status_code: int = 400
    error_code: str = "BAD_REQUEST"
    default_message: str = "Unexpected error"

    def __init__(self, message: str | None = None, **details):
        self.message = message or self.default_message
        self.details = details  # repo_url, branch и т.д.
        super().__init__(self.message)