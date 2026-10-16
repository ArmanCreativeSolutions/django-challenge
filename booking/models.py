import uuid

from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Stadium(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=500)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class Match(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    stadium = models.ForeignKey(Stadium, on_delete=models.PROTECT, related_name="matches")
    home_team = models.CharField(max_length=100)
    away_team = models.CharField(max_length=100)
    starts_at = models.DateTimeField()
    status = models.CharField(max_length=12, choices=Status, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["starts_at", "id"]
        indexes = [models.Index(fields=["status", "starts_at"], name="match_status_start_idx")]
        constraints = [
            models.CheckConstraint(condition=~Q(home_team=F("away_team")), name="different_teams"),
            models.CheckConstraint(
                condition=Q(status__in=["draft", "published"]), name="valid_match_status"
            ),
        ]

    def __str__(self):
        return f"{self.home_team} vs {self.away_team}"


class MatchSeat(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="seats")
    section = models.CharField(max_length=40)
    row = models.CharField(max_length=20)
    number = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["section", "row", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["match", "section", "row", "number"], name="unique_match_seat_location"
            ),
            models.UniqueConstraint(fields=["id", "match"], name="seat_id_match_unique"),
            models.CheckConstraint(condition=Q(price__gte=0), name="nonnegative_seat_price"),
            models.CheckConstraint(condition=Q(number__gte=1), name="positive_seat_number"),
        ]

    def __str__(self):
        return f"Match {self.match_id}: {self.section}/{self.row}/{self.number}"


class Ticket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    match = models.ForeignKey(Match, on_delete=models.PROTECT, related_name="tickets")
    seat = models.OneToOneField(MatchSeat, on_delete=models.PROTECT, related_name="ticket")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=["user", "match"], name="one_ticket_per_user_match"),
            models.CheckConstraint(condition=Q(price__gte=0), name="nonnegative_ticket_price"),
        ]
        indexes = [models.Index(fields=["user", "-created_at"], name="ticket_user_created_idx")]


class IdempotencyRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    key = models.CharField(max_length=128)
    fingerprint = models.CharField(max_length=64)
    response = models.JSONField()
    status_code = models.PositiveSmallIntegerField(default=201)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "key"], name="unique_user_idempotency_key")
        ]
