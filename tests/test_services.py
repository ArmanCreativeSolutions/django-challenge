from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from booking.domain.contracts import (
    BuyerRepository,
    ReplayRepository,
    SeatMapCache,
    SeatRepository,
    TicketRepository,
)
from booking.domain.data_objects import MatchData, ReplayData, SeatData, TicketData
from booking.services.booking_service import BookingService
from shared.application_errors import (
    ConflictError,
    ForbiddenError,
    PersistenceConflict,
    ValidationError,
)
from shared.contracts import Clock


class DeferredTransactions:
    def __init__(self):
        self.callbacks = []

    @contextmanager
    def atomic(self):
        yield

    def after_commit(self, callback):
        self.callbacks.append(callback)


@pytest.fixture
def service():
    now = datetime(2030, 1, 1, tzinfo=timezone.utc)
    match = MatchData(10, 1, "A", "B", now + timedelta(days=1), "published", now)
    buyers = Mock(spec=BuyerRepository)
    buyers.lock_active.return_value = True
    seats = Mock(spec=SeatRepository)
    seats.lock.return_value = SeatData(20, match, Decimal("12.50"))
    tickets = Mock(spec=TicketRepository)
    tickets.exists_for_buyer.return_value = False
    tickets.exists_for_seat.return_value = False
    tickets.create.return_value = TicketData(uuid4(), 10, 20, Decimal("12.50"), now)
    replays = Mock(spec=ReplayRepository)
    replays.get.return_value = None
    clock = Mock(spec=Clock)
    clock.now.return_value = now
    return BookingService(
        buyers=buyers,
        seats=seats,
        tickets=tickets,
        replays=replays,
        transactions=DeferredTransactions(),
        cache=Mock(spec=SeatMapCache),
        clock=clock,
    )


def test_service_can_purchase_using_only_injected_ports(service):
    order = []
    seat = service.seats.lock.return_value
    service.buyers.lock_active.side_effect = lambda _: order.append("buyer") or True
    service.seats.lock.side_effect = lambda **_: order.append("seat") or seat
    result = service.book(user_id=1, match_id=10, seat_id=20, idempotency_key="key")
    assert order == ["buyer", "seat"]
    assert result.response["price"] == "12.50"
    service.tickets.create.assert_called_once_with(
        user_id=1, match_id=10, seat_id=20, price=Decimal("12.50")
    )
    service.replays.create.assert_called_once_with(
        1, "key", ReplayData(service.fingerprint(10, 20), result.response, 201)
    )
    service.cache.invalidate.assert_not_called()
    service.transactions.callbacks[0]()
    service.cache.invalidate.assert_called_once_with(10)


def test_replay_does_not_read_inventory_or_reissue_ticket(service):
    response = {"id": "original", "price": "12.50"}
    service.replays.get.return_value = ReplayData(service.fingerprint(10, 20), response, 201)
    result = service.book(user_id=1, match_id=10, seat_id=20, idempotency_key="key")
    assert result.replayed and result.response == response
    service.seats.lock.assert_not_called()
    service.tickets.create.assert_not_called()
    assert not service.transactions.callbacks


def test_inactive_buyer_is_rejected_before_replay(service):
    service.buyers.lock_active.return_value = False
    with pytest.raises(ForbiddenError):
        service.book(user_id=1, match_id=10, seat_id=20, idempotency_key="key")
    service.replays.get.assert_not_called()


def test_conflicting_replay_key_does_not_touch_inventory(service):
    service.replays.get.return_value = ReplayData("other-fingerprint", {}, 201)
    with pytest.raises(ConflictError) as caught:
        service.book(user_id=1, match_id=10, seat_id=20, idempotency_key="key")
    assert caught.value.code == "idempotency_conflict"
    service.seats.lock.assert_not_called()


def test_known_constraint_conflict_is_translated_after_savepoint(service):
    service.tickets.exists_for_buyer.side_effect = [False, True]
    service.tickets.create.side_effect = PersistenceConflict()
    with pytest.raises(ValidationError) as caught:
        service.book(user_id=1, match_id=10, seat_id=20, idempotency_key="key")
    assert caught.value.code == "already_booked"
    service.replays.create.assert_not_called()
    assert not service.transactions.callbacks


def test_unrelated_constraint_failure_is_not_misreported(service):
    service.tickets.create.side_effect = PersistenceConflict()
    with pytest.raises(PersistenceConflict):
        service.book(user_id=1, match_id=10, seat_id=20, idempotency_key="key")
    service.replays.create.assert_not_called()
