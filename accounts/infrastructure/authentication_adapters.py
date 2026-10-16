from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from accounts.domain.data_objects import UserData
from shared.application_errors import ValidationError


class DjangoCredentialVerifier:
    def authenticate(self, *, username, password):
        user = authenticate(username=username, password=password)
        return UserData(user.pk, user.username) if user is not None else None


class DjangoRegistrationPolicy:
    def validate(self, *, username, password):
        user_model = get_user_model()
        username = user_model.normalize_username(username)
        candidate = user_model(username=username)
        try:
            user_model._meta.get_field("username").clean(username, candidate)
        except DjangoValidationError as exc:
            raise ValidationError(
                "invalid_username", "Invalid username.", fields={"username": exc.messages}
            ) from exc
        try:
            validate_password(password, candidate)
        except DjangoValidationError as exc:
            raise ValidationError(
                "invalid_password", "Invalid password.", fields={"password": exc.messages}
            ) from exc
        return username
