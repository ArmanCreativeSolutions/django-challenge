from unittest.mock import Mock, patch

import pytest
from django.db import IntegrityError, transaction

from booking.models import IdempotencyRecord, Ticket

pytestmark = pytest.mark.django_db


def test_failure_after_ticket_insert_rolls_back_everything(user, match, app):
    invalidator = Mock()
    with (
        patch.object(app.seat_maps, "invalidate", invalidator),
        patch.object(IdempotencyRecord.objects, "create", side_effect=RuntimeError("injected")),
        pytest.raises(RuntimeError, match="injected"),
    ):
        app.booking.book(
            user_id=user.pk,
            match_id=match.pk,
            seat_id=match.seats.first().pk,
            idempotency_key="rollback-test",
        )
    assert not Ticket.objects.exists()
    assert not IdempotencyRecord.objects.exists()
    invalidator.assert_not_called()


def test_cache_invalidation_runs_only_after_commit(
    user, match, app, django_capture_on_commit_callbacks
):
    invalidator = Mock()
    with patch.object(app.seat_maps, "invalidate", invalidator):
        with django_capture_on_commit_callbacks(execute=True):
            app.booking.book(
                user_id=user.pk,
                match_id=match.pk,
                seat_id=match.seats.first().pk,
                idempotency_key="commit-test",
            )
            invalidator.assert_not_called()
        invalidator.assert_called_once_with(match.pk)


def test_db_constraints_reject_duplicate_user_and_seat(user, other_user, match):
    seats = list(match.seats.all())
    Ticket.objects.create(user=user, match=match, seat=seats[0], price=seats[0].price)
    with pytest.raises(IntegrityError), transaction.atomic():
        Ticket.objects.create(user=user, match=match, seat=seats[1], price=seats[1].price)
    with pytest.raises(IntegrityError), transaction.atomic():
        Ticket.objects.create(user=other_user, match=match, seat=seats[0], price=seats[0].price)


def test_db_rejects_mismatched_ticket_seat_and_match(user, match, match_factory):
    other = match_factory()
    seat = other.seats.first()
    with pytest.raises(IntegrityError), transaction.atomic():
        Ticket.objects.create(user=user, match=match, seat=seat, price=seat.price)


@pytest.mark.django_db(transaction=True)
def test_unexpected_cache_callback_failure_cannot_fail_committed_purchase(app, purchase, match):
    app.seat_maps.invalidate.side_effect = RuntimeError("adapter failure")
    seat = match.seats.first()
    first = purchase(match, seat)
    assert first.status_code == 201
    assert purchase(match, seat).data == first.data
    assert Ticket.objects.count() == IdempotencyRecord.objects.count() == 1
