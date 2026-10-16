from datetime import timedelta

import pytest
from django.contrib import admin
from django.test import RequestFactory
from django.utils import timezone

from booking.models import Match, MatchSeat, Stadium, Ticket

pytestmark = pytest.mark.django_db

LAYOUT = {"seats": [{"section": "A", "row": "1", "number": 1, "price": "10.00"}]}


def test_staff_can_create_stadium_and_match(client, staff):
    client.force_authenticate(staff)
    stadium = client.post("/api/stadiums/", {"name": "Azadi", "address": "Tehran"})
    assert stadium.status_code == 201
    match = client.post(
        "/api/matches/",
        {
            "stadium": stadium.data["id"],
            "home_team": "A",
            "away_team": "B",
            "starts_at": (timezone.now() + timedelta(days=1)).isoformat(),
            "status": "published",
        },
    )
    assert match.status_code == 201
    assert match.data["status"] == "draft"


def test_nonstaff_cannot_write_catalog(client, user, match):
    client.force_authenticate(user)
    assert client.post("/api/stadiums/", {"name": "Arena", "address": "City"}).status_code == 403
    assert client.post("/api/matches/", {}).status_code == 403
    assert client.put(f"/api/matches/{match.pk}/layout/", LAYOUT).status_code == 403
    assert client.post(f"/api/matches/{match.pk}/publish/").status_code == 403


def test_drafts_hidden_from_public(client, match_factory):
    draft = match_factory(published=False)
    assert client.get("/api/matches/").data["count"] == 0
    assert client.get(f"/api/matches/{draft.pk}/").status_code == 404
    assert client.get(f"/api/matches/{draft.pk}/seats/").status_code == 404


def test_define_publish_and_freeze_layout(client, staff, match_factory):
    client.force_authenticate(staff)
    match = match_factory(published=False, seat_count=0)
    path = f"/api/matches/{match.pk}"
    assert client.post(f"{path}/publish/").status_code == 400
    assert client.put(f"{path}/layout/", LAYOUT).status_code == 200
    assert match.seats.count() == 1
    assert client.post(f"{path}/publish/").status_code == 200
    assert client.post(f"{path}/publish/").status_code == 200
    assert client.put(f"{path}/layout/", LAYOUT).status_code == 409
    assert client.patch(f"{path}/", {"status": "draft"}).status_code == 405
    assert client.delete(f"{path}/").status_code == 405


def test_invalid_layout_does_not_remove_existing_seats(client, staff, match_factory):
    client.force_authenticate(staff)
    match = match_factory(published=False)
    path = f"/api/matches/{match.pk}/layout/"
    assert client.put(path, {"seats": LAYOUT["seats"] * 2}).status_code == 400
    assert client.put(path, {"seats": []}).status_code == 400
    invalid = {"seats": [{"section": "A", "row": "1", "number": 0, "price": "-1"}]}
    assert client.put(path, invalid).status_code == 400
    assert match.seats.count() == 3


def test_admin_cannot_bypass_booking_service(staff):
    request = RequestFactory().get("/admin/")
    request.user = staff
    for model in (Match, MatchSeat, Ticket):
        model_admin = admin.site._registry[model]
        assert not model_admin.has_add_permission(request)
        assert not model_admin.has_change_permission(request)
        assert not model_admin.has_delete_permission(request)


def test_repository_pagination_has_correct_links_and_boundaries(client):
    Stadium.objects.bulk_create([Stadium(name=f"Arena {i}", address="Tehran") for i in range(51)])
    first = client.get("/api/stadiums/")
    assert first.data["count"] == 51 and len(first.data["results"]) == 50
    assert first.data["next"].endswith("?page=2")
    assert first.data["previous"] is None
    second = client.get("/api/stadiums/?page=2")
    assert len(second.data["results"]) == 1 and second.data["next"] is None
    assert second.data["previous"].endswith("/api/stadiums/")
    for page in ("bad", "0", "-1", "3"):
        assert client.get(f"/api/stadiums/?page={page}").status_code == 404


def test_invalid_resource_identifiers_are_404(client, user):
    client.force_authenticate(user)
    for path in ("stadiums/not-an-id", "matches/99999999999999999999999", "tickets/not-a-uuid"):
        assert client.get(f"/api/{path}/").status_code == 404
