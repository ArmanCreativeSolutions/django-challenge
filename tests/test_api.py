from datetime import timedelta
from unittest.mock import patch

import pytest
from django.db import OperationalError
from django.utils import timezone

from booking.models import IdempotencyRecord, Ticket

pytestmark = pytest.mark.django_db


def test_purchase_returns_price_from_database(purchase, match, user):
    seat = match.seats.first()
    response = purchase(match, seat)
    assert response.status_code == 201
    assert response.data["price"] == "25.50"
    assert response["Idempotency-Replayed"] == "false"
    ticket = Ticket.objects.get()
    assert (ticket.user_id, ticket.match_id, ticket.seat_id) == (user.pk, match.pk, seat.pk)
    assert IdempotencyRecord.objects.get().response == response.data


def test_same_request_replays_exact_response(purchase, match):
    seat = match.seats.first()
    first = purchase(match, seat)
    second = purchase(match, seat)
    assert second.status_code == 201
    assert second.data == first.data
    assert second["Idempotency-Replayed"] == "true"
    assert Ticket.objects.count() == IdempotencyRecord.objects.count() == 1


def test_replay_still_works_after_match_started(purchase, match):
    seat = match.seats.first()
    first = purchase(match, seat)
    match.starts_at = timezone.now() - timedelta(hours=1)
    match.save(update_fields=["starts_at"])
    assert purchase(match, seat).data == first.data


def test_one_ticket_per_user_per_match(purchase, match):
    seats = list(match.seats.all())
    assert purchase(match, seats[0]).status_code == 201
    response = purchase(match, seats[1], key="new-request")
    assert response.status_code == 400
    assert response.data["code"] == "already_booked"
    assert Ticket.objects.count() == 1


def test_seat_cannot_be_sold_twice(purchase, match, other_user):
    seat = match.seats.first()
    assert purchase(match, seat).status_code == 201
    response = purchase(match, seat, buyer=other_user)
    assert response.status_code == 409
    assert response.data["code"] == "seat_unavailable"


def test_key_cannot_be_reused_for_another_payload(purchase, match, match_factory):
    seats = list(match.seats.all())
    purchase(match, seats[0])
    assert purchase(match, seats[1]).status_code == 409
    another = match_factory()
    response = purchase(another, another.seats.first())
    assert response.status_code == 409
    assert response.data["code"] == "idempotency_conflict"


def test_key_is_scoped_to_user(purchase, match, other_user):
    seats = list(match.seats.all())
    assert purchase(match, seats[0]).status_code == 201
    assert purchase(match, seats[1], buyer=other_user).status_code == 201
    assert IdempotencyRecord.objects.count() == 2


def test_user_can_book_distinct_matches(purchase, match, match_factory):
    assert purchase(match, match.seats.first()).status_code == 201
    other = match_factory()
    assert purchase(other, other.seats.first(), key="request-2").status_code == 201


@pytest.mark.parametrize("key", ["", " ", "a b", "x" * 129, "invalid\tkey"])
def test_invalid_idempotency_headers_rejected(purchase, match, key):
    assert purchase(match, match.seats.first(), key=key).status_code == 400
    assert not Ticket.objects.exists()


def test_authentication_required(client, match):
    assert (
        client.post(
            f"/api/matches/{match.pk}/bookings/",
            {"seat_id": match.seats.first().pk},
            HTTP_IDEMPOTENCY_KEY="anonymous-request",
        ).status_code
        == 401
    )


def test_missing_header_and_invalid_seat_input(client, user, match):
    client.force_authenticate(user)
    path = f"/api/matches/{match.pk}/bookings/"
    assert client.post(path, {"seat_id": 1}).status_code == 400
    assert client.post(path, {"seat_id": -1}, HTTP_IDEMPOTENCY_KEY="valid").status_code == 400


def test_seat_from_other_match_not_found(purchase, match, match_factory):
    other = match_factory()
    assert purchase(match, other.seats.first()).status_code == 404
    assert not Ticket.objects.exists()


def test_draft_and_past_matches_not_bookable(purchase, match_factory):
    draft = match_factory(published=False)
    assert purchase(draft, draft.seats.first()).status_code == 404
    past = match_factory(starts_at=timezone.now() - timedelta(hours=1))
    response = purchase(past, past.seats.first())
    assert response.status_code == 400
    assert response.data["code"] == "sales_closed"


def test_failed_request_does_not_consume_key(purchase, match, other_user):
    seats = list(match.seats.all())
    purchase(match, seats[0], buyer=other_user)
    assert purchase(match, seats[0]).status_code == 409
    assert purchase(match, seats[1]).status_code == 201


def test_ticket_list_and_detail_only_show_current_user(client, purchase, match, other_user):
    response = purchase(match, match.seats.first())
    ticket_id = response.data["id"]
    assert client.get("/api/tickets/").data["count"] == 1
    client.force_authenticate(other_user)
    assert client.get("/api/tickets/").data["count"] == 0
    assert client.get(f"/api/tickets/{ticket_id}/").status_code == 404


def test_database_timeout_returns_retryable_503(purchase, match, app):
    seat = match.seats.first()
    with patch.object(app.booking, "book", side_effect=OperationalError("lock timeout")):
        response = purchase(match, seat)
    assert response.status_code == 503
    assert response["Retry-After"] == "1"
