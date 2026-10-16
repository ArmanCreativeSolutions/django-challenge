import hashlib
import json
import re
from functools import partial

from booking.domain.contracts import (
    BuyerRepository,
    ReplayRepository,
    SeatMapCache,
    SeatRepository,
    TicketRepository,
)
from booking.domain.data_objects import BookingResult, ReplayData
from shared.application_errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    PersistenceConflict,
    ValidationError,
)
from shared.contracts import Clock, TransactionManager


class BookingService:
    def __init__(
        self,
        *,
        buyers: BuyerRepository,
        seats: SeatRepository,
        tickets: TicketRepository,
        replays: ReplayRepository,
        transactions: TransactionManager,
        cache: SeatMapCache,
        clock: Clock,
    ):
        self.buyers = buyers
        self.seats = seats
        self.tickets = tickets
        self.replays = replays
        self.transactions = transactions
        self.cache = cache
        self.clock = clock

    @staticmethod
    def fingerprint(match_id: int, seat_id: int) -> str:
        payload = json.dumps(
            {"operation": "book-seat-v1", "match_id": match_id, "seat_id": seat_id},
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def book(self, *, user_id: int, match_id: int, seat_id: int, idempotency_key: str):
        if not re.fullmatch(r"[\x21-\x7e]{1,128}", idempotency_key):
            raise ValidationError(
                "invalid_idempotency_key", "Provide a valid Idempotency-Key header."
            )
        fingerprint = self.fingerprint(match_id, seat_id)
        with self.transactions.atomic():
            # The order matters: buyer first, then seat; never lock the whole match.
            if not self.buyers.lock_active(user_id):
                raise ForbiddenError("inactive_user", "This account is inactive.")
            previous = self.replays.get(user_id, idempotency_key)
            if previous is not None:
                if previous.fingerprint != fingerprint:
                    raise ConflictError(
                        "idempotency_conflict", "This key was already used for another request."
                    )
                return BookingResult(previous.response, previous.status_code, replayed=True)

            seat = self.seats.lock(match_id=match_id, seat_id=seat_id)
            if seat is None:
                raise NotFoundError("seat_not_found", "No such seat in this match.")
            if not seat.match.sales_open(self.clock.now()):
                raise ValidationError("sales_closed", "Ticket sales are not open for this match.")
            self.check_conflicts(user_id=user_id, match_id=match_id, seat_id=seat_id)
            try:
                # A nested transaction creates a savepoint before a constraint can fail.
                with self.transactions.atomic():
                    ticket = self.tickets.create(
                        user_id=user_id, match_id=match_id, seat_id=seat.id, price=seat.price
                    )
            except PersistenceConflict:
                self.check_conflicts(user_id=user_id, match_id=match_id, seat_id=seat_id)
                raise  # Unexpected integrity failures must not look like a sold seat.

            response = ticket.to_record()
            self.replays.create(user_id, idempotency_key, ReplayData(fingerprint, response, 201))
            self.transactions.after_commit(partial(self.cache.invalidate, match_id))
            return BookingResult(response)

    def check_conflicts(self, *, user_id: int, match_id: int, seat_id: int):
        if self.tickets.exists_for_buyer(user_id=user_id, match_id=match_id):
            raise ValidationError("already_booked", "You already have a ticket for this match.")
        if self.tickets.exists_for_seat(seat_id):
            raise ConflictError("seat_unavailable", "This seat is already booked.")
