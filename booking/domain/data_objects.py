from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class StadiumData:
    id: int
    name: str
    address: str


@dataclass(frozen=True)
class MatchData:
    id: int
    stadium: int
    home_team: str
    away_team: str
    starts_at: datetime
    status: str
    created_at: datetime

    def sales_open(self, now: datetime) -> bool:
        return self.status == "published" and self.starts_at > now


@dataclass(frozen=True)
class SeatDefinition:
    section: str
    row: str
    number: int
    price: Decimal


@dataclass(frozen=True)
class SeatData:
    id: int
    match: MatchData
    price: Decimal


@dataclass(frozen=True)
class TicketData:
    id: UUID
    match_id: int
    seat_id: int
    price: Decimal
    created_at: datetime

    def to_record(self) -> dict:
        return {
            "id": str(self.id),
            "match_id": self.match_id,
            "seat_id": self.seat_id,
            "price": str(self.price),
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class ReplayData:
    fingerprint: str
    response: dict
    status_code: int


@dataclass(frozen=True)
class BookingResult:
    response: dict
    status_code: int = 201
    replayed: bool = False
