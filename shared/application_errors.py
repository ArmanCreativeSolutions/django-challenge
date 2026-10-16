class ApplicationError(Exception):
    def __init__(self, code: str, message: str, *, fields: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.fields = fields


class ValidationError(ApplicationError):
    pass


class NotFoundError(ApplicationError):
    pass


class ConflictError(ApplicationError):
    pass


class ForbiddenError(ApplicationError):
    pass


class AuthenticationError(ApplicationError):
    pass


class ServiceUnavailableError(ApplicationError):
    def __init__(self, message="Temporarily unavailable. Retry with the same idempotency key."):
        super().__init__("temporarily_unavailable", message)


class PersistenceConflict(Exception):
    """An integrity constraint failed; callers may translate known conflicts only."""
