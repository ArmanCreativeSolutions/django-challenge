from datetime import timedelta
from decimal import Decimal
from unittest.mock import Mock

import pytest
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient

from booking.models import Match, MatchSeat, Stadium
from shared.api.dependency_injection import DependencyMixin
from volleyball_ticketing.dependency_container import ApplicationContainer


@pytest.fixture(autouse=True)
def isolate_tests(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    cache.clear()


@pytest.fixture(autouse=True)
def app(monkeypatch):
    # An explicit composition root override; no hidden global function patching.
    container = ApplicationContainer(seat_maps=Mock())
    monkeypatch.setattr(DependencyMixin, "dependencies", container)
    return container


@pytest.fixture
def client(app):
    return APIClient()


@pytest.fixture
def user(db, django_user_model):
    return django_user_model.objects.create_user(username="buyer", password="strong-password-932")


@pytest.fixture
def other_user(db, django_user_model):
    return django_user_model.objects.create_user(username="other", password="strong-password-842")


@pytest.fixture
def staff(db, django_user_model):
    return django_user_model.objects.create_user(
        username="staff", password="strong-password-176", is_staff=True
    )


@pytest.fixture
def match_factory(db):
    def create(*, published=True, seat_count=3, starts_at=None):
        stadium = Stadium.objects.create(name="Arena", address="Tehran")
        match = Match.objects.create(
            stadium=stadium,
            home_team="Falcons",
            away_team="Waves",
            starts_at=starts_at or timezone.now() + timedelta(days=2),
            status=Match.Status.PUBLISHED if published else Match.Status.DRAFT,
        )
        MatchSeat.objects.bulk_create(
            [
                MatchSeat(match=match, section="A", row="1", number=i + 1, price=Decimal("25.50"))
                for i in range(seat_count)
            ]
        )
        return match

    return create


@pytest.fixture
def match(match_factory):
    return match_factory()


@pytest.fixture
def purchase(client, user):
    def buy(match, seat, key="request-1", buyer=None):
        client.force_authenticate(user=buyer or user)
        return client.post(
            f"/api/matches/{match.pk}/bookings/",
            {"seat_id": seat.pk},
            HTTP_IDEMPOTENCY_KEY=key,
        )

    return buy
