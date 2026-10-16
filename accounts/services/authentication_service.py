from accounts.domain.contracts import (
    CredentialVerifier,
    RegistrationPolicy,
    TokenRepository,
    UserRepository,
)
from accounts.domain.data_objects import AuthResult
from shared.application_errors import AuthenticationError, PersistenceConflict, ValidationError
from shared.contracts import TransactionManager


class AuthenticationService:
    def __init__(
        self,
        *,
        users: UserRepository,
        tokens: TokenRepository,
        credentials: CredentialVerifier,
        registration: RegistrationPolicy,
        transactions: TransactionManager,
    ):
        self.users = users
        self.tokens = tokens
        self.credentials = credentials
        self.registration = registration
        self.transactions = transactions

    def signup(self, *, username: str, password: str):
        username = self.registration.validate(username=username, password=password)
        if self.users.username_exists(username):
            raise self.duplicate_username()
        try:
            with self.transactions.atomic():
                user = self.users.create(username=username, password=password)
                return AuthResult(self.tokens.get_or_create(user.id), user)
        except PersistenceConflict:
            # A concurrent signup can win after the optimistic existence check.
            if self.users.username_exists(username):
                raise self.duplicate_username() from None
            raise

    @staticmethod
    def duplicate_username():
        return ValidationError(
            "username_taken",
            "This username is already registered.",
            fields={"username": ["This username is already registered."]},
        )

    def login(self, *, username: str, password: str):
        user = self.credentials.authenticate(username=username, password=password)
        if user is None:
            raise AuthenticationError("invalid_credentials", "Invalid username or password.")
        with self.transactions.atomic():
            return AuthResult(self.tokens.get_or_create(user.id), user)

    def logout(self, *, token: str):
        with self.transactions.atomic():
            self.tokens.revoke(token)
