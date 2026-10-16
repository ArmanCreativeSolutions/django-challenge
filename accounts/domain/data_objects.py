from dataclasses import dataclass


@dataclass(frozen=True)
class UserData:
    id: int
    username: str


@dataclass(frozen=True)
class AuthResult:
    token: str
    user: UserData
