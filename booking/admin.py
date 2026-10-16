from django.contrib import admin

from .models import IdempotencyRecord, Match, MatchSeat, Stadium, Ticket


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Stadium)
class StadiumAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "address"]
    search_fields = ["name"]


@admin.register(Match)
class MatchAdmin(ReadOnlyAdmin):
    list_display = ["id", "home_team", "away_team", "stadium", "starts_at", "status"]
    list_filter = ["status"]
    list_select_related = ["stadium"]


@admin.register(MatchSeat)
class MatchSeatAdmin(ReadOnlyAdmin):
    list_display = ["id", "match", "section", "row", "number", "price"]
    list_select_related = ["match"]
    search_fields = ["match__home_team", "section"]


@admin.register(Ticket)
class TicketAdmin(ReadOnlyAdmin):
    list_display = ["id", "user", "match", "seat", "price", "created_at"]
    list_select_related = ["user", "match", "seat"]
    search_fields = ["user__username"]


@admin.register(IdempotencyRecord)
class IdempotencyAdmin(ReadOnlyAdmin):
    list_display = ["id", "user", "key", "status_code", "created_at"]
    list_select_related = ["user"]
