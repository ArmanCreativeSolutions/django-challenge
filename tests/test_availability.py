import json
import os
import uuid
from unittest.mock import Mock

import pytest
from redis import Redis
from redis.exceptions import ConnectionError

from booking.infrastructure.redis_seat_map_cache import RedisSeatMapCache
from booking.models import Ticket
from shared.api.dependency_injection import DependencyMixin
from shared.application_errors import ServiceUnavailableError
from volleyball_ticketing.dependency_container import ApplicationContainer


@pytest.fixture
def cache_app(app, monkeypatch):
    adapter = RedisSeatMapCache(client=Mock(), ttl=10, lock_ttl=15)
    container = ApplicationContainer(seat_maps=adapter)
    monkeypatch.setattr(DependencyMixin, "dependencies", container)
    return container


def test_redis_outage_sheds_browse_load_without_querying_postgres(cache_app):
    cache_app.seat_maps.client.get.side_effect = ConnectionError("offline")
    cache_app.availability.seats = Mock()
    with pytest.raises(ServiceUnavailableError):
        cache_app.availability.snapshot(1)
    cache_app.availability.seats.availability.assert_not_called()


def test_cold_cache_competitors_do_not_all_query_database(cache_app):
    redis = cache_app.seat_maps.client
    redis.get.return_value = None
    redis.lock.return_value.acquire.return_value = False
    cache_app.availability.seats = Mock()
    with pytest.raises(ServiceUnavailableError):
        cache_app.availability.snapshot(1)
    cache_app.availability.seats.availability.assert_not_called()


@pytest.mark.django_db
def test_warm_cache_avoids_seat_query(cache_app, match, django_assert_num_queries):
    snapshot = cache_app.availability.build_snapshot(match.pk)
    cache_app.seat_maps.client.get.return_value = json.dumps(snapshot)
    with django_assert_num_queries(0):
        assert cache_app.availability.snapshot(match.pk) == snapshot


@pytest.mark.django_db
def test_seat_map_query_count_is_constant(app, match, django_assert_num_queries):
    with django_assert_num_queries(1):
        snapshot = app.availability.build_snapshot(match.pk)
    assert snapshot["available_count"] == match.seats.count()
    assert "user_id" not in json.dumps(snapshot)


def test_invalidation_failure_is_nonfatal(cache_app):
    cache_app.seat_maps.client.delete.side_effect = ConnectionError("offline")
    cache_app.seat_maps.invalidate(1)


@pytest.mark.django_db(transaction=True)
def test_committed_purchase_survives_redis_outage(cache_app, purchase, match):
    cache_app.seat_maps.client.delete.side_effect = ConnectionError("offline")
    seat = match.seats.first()
    first = purchase(match, seat)
    assert first.status_code == 201
    assert purchase(match, seat).data == first.data
    assert Ticket.objects.count() == 1


@pytest.mark.parametrize("cached", ["broken-json", "[]", '{"match_id": 2}'])
def test_corrupt_or_wrong_match_cache_is_retryable(cache_app, cached):
    cache_app.seat_maps.client.get.return_value = cached
    with pytest.raises(ServiceUnavailableError):
        cache_app.availability.snapshot(1)


@pytest.fixture
def real_app(app, monkeypatch):
    url = os.getenv("TEST_REDIS_URL")
    if not url:
        pytest.skip("Set TEST_REDIS_URL to a test Redis instance to run integration tests.")
    client = Redis.from_url(url, decode_responses=True, socket_timeout=1)
    client.ping()
    prefix = f"ticketing-test:{uuid.uuid4().hex}"
    adapter = RedisSeatMapCache(client=client, ttl=10, lock_ttl=15, prefix=prefix)
    container = ApplicationContainer(seat_maps=adapter)
    monkeypatch.setattr(DependencyMixin, "dependencies", container)
    yield container
    keys = list(client.scan_iter(f"{prefix}:*"))
    if keys:
        client.delete(*keys)
    client.close()


@pytest.mark.redis
@pytest.mark.django_db(transaction=True)
def test_real_redis_cache_is_invalidated_after_purchase(real_app, client, purchase, match):
    path = f"/api/matches/{match.pk}/seats/"
    response = client.get(path)
    assert response.status_code == 200
    assert response.data["available_count"] == 3
    seat = match.seats.first()
    assert purchase(match, seat).status_code == 201
    response = client.get(path)
    assert response.status_code == 200
    assert response.data["available_count"] == 2
    booked_seat = next(item for item in response.data["seats"] if item["id"] == seat.pk)
    assert not booked_seat["available"]


@pytest.mark.redis
@pytest.mark.django_db(transaction=True)
def test_stale_redis_snapshot_cannot_authorize_duplicate_sale(
    real_app, purchase, match, other_user
):
    seat = match.seats.first()
    stale_snapshot = real_app.availability.snapshot(match.pk)
    assert purchase(match, seat).status_code == 201
    cache = real_app.seat_maps
    cache.client.set(cache.key(match.pk), json.dumps(stale_snapshot), ex=10)
    assert real_app.availability.snapshot(match.pk)["available_count"] == 3
    assert purchase(match, seat, buyer=other_user).status_code == 409
    assert Ticket.objects.count() == 1
