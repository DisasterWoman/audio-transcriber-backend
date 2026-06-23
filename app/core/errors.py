class AppError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class BadRequestError(AppError):
    status_code = 400
    code = "bad_request"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class FileTooLargeError(AppError):
    status_code = 413
    code = "file_too_large"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ServiceUnavailableError(AppError):
    status_code = 503
    code = "service_unavailable"
