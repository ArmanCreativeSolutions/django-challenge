import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

pytestmark = pytest.mark.django_db


def test_signup_hashes_password_and_issues_usable_token(client):
    response = client.post(
        "/api/auth/signup/", {"username": "new-buyer", "password": "sunrise-secret-9382"}
    )
    assert response.status_code == 201
    user = get_user_model().objects.get(username="new-buyer")
    assert user.check_password("sunrise-secret-9382")
    assert "password" not in response.data
    client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
    assert client.get("/api/tickets/").status_code == 200


def test_weak_password_and_duplicate_username_rejected(client, user):
    assert (
        client.post("/api/auth/signup/", {"username": "weak-user", "password": "123"}).status_code
        == 400
    )
    assert (
        client.post(
            "/api/auth/signup/", {"username": user.username, "password": "another-secret-972"}
        ).status_code
        == 400
    )


def test_signup_cannot_grant_staff_privileges(client):
    response = client.post(
        "/api/auth/signup/",
        {"username": "try-staff", "password": "other-secret-2145", "is_staff": True},
    )
    assert response.status_code == 201
    assert not get_user_model().objects.get(username="try-staff").is_staff


def test_login_logout_and_revocation(client, user):
    response = client.post(
        "/api/auth/login/", {"username": user.username, "password": "strong-password-932"}
    )
    assert response.status_code == 200
    token = response.data["token"]
    client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
    assert client.post("/api/auth/logout/").status_code == 204
    assert not Token.objects.filter(key=token).exists()
    assert client.get("/api/tickets/").status_code == 401


def test_invalid_login_and_inactive_account(client, user):
    data = {"username": user.username, "password": "wrong"}
    assert client.post("/api/auth/login/", data).status_code == 401
    user.is_active = False
    user.save(update_fields=["is_active"])
    data["password"] = "strong-password-932"
    assert client.post("/api/auth/login/", data).status_code == 401
