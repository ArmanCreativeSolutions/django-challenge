from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Generic, Protocol, TypeVar

from .application_errors import NotFoundError

T = TypeVar("T")


class Clock(Protocol):
    def now(self) -> datetime: ...


class TransactionManager(Protocol):
    def atomic(self) -> AbstractContextManager[None]: ...

    def after_commit(self, callback: Callable[[], None]) -> None: ...


@dataclass(frozen=True)
class PageRequest:
    number: int = 1
    size: int = 50

    def __post_init__(self):
        if self.number < 1 or not 1 <= self.size <= 100:
            raise NotFoundError("invalid_page", "Invalid page.")

    @property
    def offset(self) -> int:
        return (self.number - 1) * self.size

    def check_count(self, count: int) -> None:
        if self.number > 1 and self.offset >= count:
            raise NotFoundError("invalid_page", "Invalid page.")


@dataclass(frozen=True)
class Page(Generic[T]):
    items: list[T]
    count: int
    request: PageRequest
