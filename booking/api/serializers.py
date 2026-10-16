from django.conf import settings
from rest_framework import serializers


class StadiumSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=200)
    address = serializers.CharField(max_length=500)


class MatchSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    stadium = serializers.IntegerField(min_value=1)
    home_team = serializers.CharField(max_length=100)
    away_team = serializers.CharField(max_length=100)
    starts_at = serializers.DateTimeField()
    status = serializers.ChoiceField(choices=["draft", "published"], read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class SeatInputSerializer(serializers.Serializer):
    section = serializers.CharField(max_length=40)
    row = serializers.CharField(max_length=20)
    number = serializers.IntegerField(min_value=1, max_value=2147483647)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)


class LayoutSerializer(serializers.Serializer):
    seats = SeatInputSerializer(many=True, allow_empty=False, max_length=settings.SEAT_MAP_MAX_SIZE)


class LayoutResponseSerializer(serializers.Serializer):
    match_id = serializers.IntegerField()
    seat_count = serializers.IntegerField()


class BookingInputSerializer(serializers.Serializer):
    seat_id = serializers.IntegerField(min_value=1)


class TicketSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    match_id = serializers.IntegerField(read_only=True)
    seat_id = serializers.IntegerField(read_only=True)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class SeatMapSeatSerializer(SeatInputSerializer):
    id = serializers.IntegerField()
    available = serializers.BooleanField()


class SeatMapSerializer(serializers.Serializer):
    match_id = serializers.IntegerField()
    generated_at = serializers.DateTimeField()
    cache_ttl_seconds = serializers.IntegerField()
    available_count = serializers.IntegerField()
    sales_open = serializers.BooleanField()
    seats = SeatMapSeatSerializer(many=True)


class ErrorSerializer(serializers.Serializer):
    code = serializers.CharField()
    detail = serializers.CharField()
    errors = serializers.JSONField(required=False)


class HealthSerializer(serializers.Serializer):
    status = serializers.CharField()
