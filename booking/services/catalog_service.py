from datetime import datetime
from decimal import Decimal
from functools import partial

from booking.domain.contracts import (
    MatchRepository,
    SeatMapCache,
    SeatRepository,
    StadiumRepository,
)
from booking.domain.data_objects import SeatDefinition
from shared.application_errors import ConflictError, NotFoundError, ValidationError
from shared.contracts import Clock, PageRequest, TransactionManager


class CatalogService:
    def __init__(
        self,
        *,
        stadiums: StadiumRepository,
        matches: MatchRepository,
        seats: SeatRepository,
        transactions: TransactionManager,
        cache: SeatMapCache,
        clock: Clock,
        max_seats: int,
    ):
        self.stadiums = stadiums
        self.matches = matches
        self.seats = seats
        self.transactions = transactions
        self.cache = cache
        self.clock = clock
        self.max_seats = max_seats

    def list_stadiums(self, page: PageRequest):
        return self.stadiums.list(page)

    def get_stadium(self, stadium_id: int):
        stadium = self.stadiums.get(stadium_id)
        if stadium is None:
            raise NotFoundError("stadium_not_found", "No such stadium.")
        return stadium

    def create_stadium(self, *, name: str, address: str):
        with self.transactions.atomic():
            return self.stadiums.create(name=name, address=address)

    def list_matches(self, page: PageRequest, *, include_drafts: bool = False):
        return self.matches.list(page, include_drafts=include_drafts)

    def get_match(self, match_id: int, *, include_drafts: bool = False):
        match = self.matches.get(match_id)
        if match is None or (not include_drafts and match.status != "published"):
            raise NotFoundError("match_not_found", "No such match.")
        return match

    def create_match(self, *, stadium: int, home_team: str, away_team: str, starts_at: datetime):
        if starts_at <= self.clock.now():
            raise ValidationError("invalid_start_time", "The match must start in the future.")
        if home_team.casefold() == away_team.casefold():
            raise ValidationError("invalid_teams", "Home and away teams must be different.")
        with self.transactions.atomic():
            if self.stadiums.get(stadium) is None:
                raise ValidationError("invalid_stadium", "No such stadium.")
            return self.matches.create(
                stadium=stadium, home_team=home_team, away_team=away_team, starts_at=starts_at
            )

    def replace_layout(self, *, match_id: int, seats: list[SeatDefinition]):
        self.validate_layout(seats)
        with self.transactions.atomic():
            match = self.matches.get(match_id, for_update=True)
            if match is None:
                raise NotFoundError("match_not_found", "No such match.")
            if match.status != "draft":
                raise ConflictError("layout_frozen", "Published seat layouts cannot be changed.")
            if match.starts_at <= self.clock.now():
                raise ValidationError("match_started", "The match has already started.")
            self.seats.replace(match_id, seats)
            self.transactions.after_commit(partial(self.cache.invalidate, match_id))
            return {"match_id": match_id, "seat_count": len(seats)}

    def validate_layout(self, seats: list[SeatDefinition]):
        if not 1 <= len(seats) <= self.max_seats:
            raise ValidationError(
                "invalid_layout", f"Provide between 1 and {self.max_seats} seats."
            )
        locations = set()
        for seat in seats:
            if (
                not 1 <= len(seat.section) <= 40
                or not 1 <= len(seat.row) <= 20
                or not 1 <= seat.number <= 2147483647
                or not seat.price.is_finite()
                or not 0 <= seat.price <= Decimal("9999999999.99")
                or seat.price.as_tuple().exponent < -2
            ):
                raise ValidationError("invalid_layout", "Invalid seat location or price.")
            location = (seat.section, seat.row, seat.number)
            if location in locations:
                raise ValidationError("duplicate_seat", "Each section/row/number must be unique.")
            locations.add(location)

    def publish(self, *, match_id: int):
        with self.transactions.atomic():
            match = self.matches.get(match_id, for_update=True)
            if match is None:
                raise NotFoundError("match_not_found", "No such match.")
            if match.status == "published":
                return match
            if match.starts_at <= self.clock.now():
                raise ValidationError("match_started", "The match has already started.")
            if not self.seats.exists_for_match(match_id):
                raise ValidationError("empty_layout", "Define a seat layout before publishing.")
            match = self.matches.publish(match_id)
            self.transactions.after_commit(partial(self.cache.invalidate, match_id))
            return match
