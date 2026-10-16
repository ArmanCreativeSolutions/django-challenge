import logging

from django.db import OperationalError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.views import set_rollback

from shared.application_errors import (
    ApplicationError,
    AuthenticationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class ApiExceptionHandler:
    status_by_type = {
        ValidationError: 400,
        AuthenticationError: 401,
        ForbiddenError: 403,
        NotFoundError: 404,
        ConflictError: 409,
        ServiceUnavailableError: 503,
    }

    def __call__(self, exc, context):
        set_rollback()
        if isinstance(exc, OperationalError):
            logger.warning("Database temporarily unavailable", exc_info=True)
            exc = ServiceUnavailableError()
        if isinstance(exc, ApplicationError):
            status = next(
                (value for kind, value in self.status_by_type.items() if isinstance(exc, kind)),
                500,
            )
            if status == 500:
                return self.unexpected(exc)
            data = {"code": exc.code, "detail": exc.message}
            if exc.fields is not None:
                data["errors"] = exc.fields
            headers = {}
            if status == 503:
                logger.warning(
                    "Dependency temporarily unavailable", exc_info=exc.__cause__ is not None
                )
                headers["Retry-After"] = "1"
            elif status == 401:
                headers["WWW-Authenticate"] = "Token"
            return Response(data, status=status, headers=headers)

        response = drf_exception_handler(exc, context)
        if response is None:
            return self.unexpected(exc)
        codes = exc.get_codes() if hasattr(exc, "get_codes") else None
        fallback = {403: "permission_denied", 404: "not_found"}.get(
            response.status_code, "validation_error"
        )
        code = codes if isinstance(codes, str) else fallback
        if isinstance(response.data, dict) and "detail" in response.data:
            response.data = {"code": code, "detail": response.data["detail"]}
        else:
            response.data = {
                "code": code,
                "detail": "Invalid request.",
                "errors": response.data,
            }
        return response

    def unexpected(self, exc):
        logger.error("Unhandled API error", exc_info=(type(exc), exc, exc.__traceback__))
        return Response(
            {"code": "internal_error", "detail": "An unexpected error occurred."}, status=500
        )


exception_handler = ApiExceptionHandler()
