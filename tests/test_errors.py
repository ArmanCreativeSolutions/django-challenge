from unittest.mock import patch

import pytest
from rest_framework.exceptions import NotAuthenticated, Throttled
from rest_framework.settings import api_settings

from shared.api.exception_handler import ApiExceptionHandler
from shared.application_errors import (
    AuthenticationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
    ValidationError,
)


def test_drf_uses_the_class_based_handler():
    assert isinstance(api_settings.EXCEPTION_HANDLER, ApiExceptionHandler)


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (ValidationError("invalid", "Invalid input."), 400),
        (AuthenticationError("invalid_credentials", "Invalid credentials."), 401),
        (ForbiddenError("inactive_user", "Inactive account."), 403),
        (NotFoundError("seat_not_found", "No such seat."), 404),
        (ConflictError("seat_unavailable", "Already sold."), 409),
        (ServiceUnavailableError(), 503),
    ],
)
def test_application_errors_are_mapped_at_http_boundary(error, status):
    response = ApiExceptionHandler()(error, {})
    assert response.status_code == status
    assert response.data == {"code": error.code, "detail": error.message}
    if status == 503:
        assert response["Retry-After"] == "1"
    if status == 401:
        assert response["WWW-Authenticate"] == "Token"


def test_framework_error_headers_are_preserved():
    error = NotAuthenticated()
    error.auth_header = "Token"
    response = ApiExceptionHandler()(error, {})
    assert response["WWW-Authenticate"] == "Token"
    assert response.data["code"] == "not_authenticated"
    response = ApiExceptionHandler()(Throttled(wait=5), {})
    assert response.status_code == 429 and response["Retry-After"] == "5"


def test_unexpected_exception_does_not_leak_details():
    response = ApiExceptionHandler()(RuntimeError("secret database connection string"), {})
    assert response.status_code == 500
    assert response.data == {"code": "internal_error", "detail": "An unexpected error occurred."}


@pytest.mark.django_db
def test_invalid_payload_uses_same_error_envelope(client):
    response = client.post("/api/auth/signup/", {})
    assert response.status_code == 400
    assert response.data["code"] == "validation_error"
    assert set(response.data["errors"]) == {"username", "password"}


@pytest.mark.django_db
def test_signup_token_failure_rolls_back_user_and_returns_sanitized_error(
    client, app, django_user_model
):
    with patch.object(app.tokens, "get_or_create", side_effect=RuntimeError("private detail")):
        response = client.post(
            "/api/auth/signup/", {"username": "rollback-buyer", "password": "sunrise-secret-9382"}
        )
    assert response.status_code == 500
    assert response.data["code"] == "internal_error"
    assert "private detail" not in str(response.data)
    assert not django_user_model.objects.filter(username="rollback-buyer").exists()
