from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import connection, connections, transaction
from rest_framework.test import APIClient

from booking.models import IdempotencyRecord, Ticket

pytestmark = pytest.mark.django_db(transaction=True)


def race(match, requests):
    assert connection.vendor == "postgresql", "Concurrency guarantees require PostgreSQL."
    barrier = Barrier(len(requests))

    def worker(request):
        buyer, seat_id, key = request
        connections.close_all()
        try:
            client = APIClient()
            client.force_authenticate(buyer)
            barrier.wait(timeout=10)
            response = client.post(
                f"/api/matches/{match.pk}/bookings/",
                {"seat_id": seat_id},
                HTTP_IDEMPOTENCY_KEY=key,
            )
            return response.status_code, response.data, response.get("Idempotency-Replayed")
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=len(requests)) as pool:
        return list(pool.map(worker, requests, timeout=20))


def test_two_buyers_compete_for_one_seat(user, other_user, match):
    seat_id = match.seats.first().pk
    results = race(match, [(user, seat_id, "one"), (other_user, seat_id, "two")])
    assert sorted(result[0] for result in results) == [201, 409]
    assert Ticket.objects.count() == IdempotencyRecord.objects.count() == 1


def test_same_user_cannot_buy_two_seats_concurrently(user, match):
    seats = list(match.seats.all())
    results = race(match, [(user, seats[0].pk, "one"), (user, seats[1].pk, "two")])
    assert sorted(result[0] for result in results) == [201, 400]
    assert Ticket.objects.count() == 1


def test_concurrent_duplicate_click_replays_one_committed_result(user, match):
    seat_id = match.seats.first().pk
    results = race(match, [(user, seat_id, "same-key"), (user, seat_id, "same-key")])
    assert [result[0] for result in results] == [201, 201]
    assert results[0][1] == results[1][1]
    assert sorted(result[2] for result in results) == ["false", "true"]
    assert Ticket.objects.count() == IdempotencyRecord.objects.count() == 1


def test_concurrent_key_reuse_with_different_payload_is_conflict(user, match):
    seats = list(match.seats.all())
    results = race(match, [(user, seats[0].pk, "same"), (user, seats[1].pk, "same")])
    assert sorted(result[0] for result in results) == [201, 409]
    loser = next(result for result in results if result[0] == 409)
    assert loser[1]["code"] == "idempotency_conflict"


def test_burst_for_last_seat_has_one_winner(django_user_model, match):
    buyers = [django_user_model.objects.create_user(username=f"burst-{i}") for i in range(8)]
    seat_id = match.seats.first().pk
    results = race(match, [(buyer, seat_id, f"burst-{i}") for i, buyer in enumerate(buyers)])
    assert sorted(result[0] for result in results) == [201] + [409] * 7
    assert Ticket.objects.count() == 1


def test_other_buyers_and_seats_are_not_serialized_on_match(user, other_user, match, app):
    seats = list(match.seats.all())

    def second_purchase():
        connections.close_all()
        try:
            return app.booking.book(
                user_id=other_user.pk,
                match_id=match.pk,
                seat_id=seats[1].pk,
                idempotency_key="independent-2",
            )
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            app.booking.book(
                user_id=user.pk,
                match_id=match.pk,
                seat_id=seats[0].pk,
                idempotency_key="independent-1",
            )
            # The first buyer's locks remain held while the second purchase commits.
            result = pool.submit(second_purchase).result(timeout=5)
            assert result.status_code == 201
    assert Ticket.objects.count() == 2
