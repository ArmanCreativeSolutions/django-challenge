from typing import Protocol

from .data_objects import UserData


class UserRepository(Protocol):
    def username_exists(self, username: str) -> bool: ...

    def create(self, *, username: str, password: str) -> UserData: ...


class TokenRepository(Protocol):
    def get_or_create(self, user_id: int) -> str: ...

    def revoke(self, key: str) -> None: ...


class CredentialVerifier(Protocol):
    def authenticate(self, *, username: str, password: str) -> UserData | None: ...


class RegistrationPolicy(Protocol):
    def validate(self, *, username: str, password: str) -> str: ...
