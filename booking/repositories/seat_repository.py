from dataclasses import asdict

from django.db.models import Exists, OuterRef

from booking.domain.data_objects import SeatData
from booking.models import MatchSeat, Ticket

from .match_repository import DjangoMatchRepository


class DjangoSeatRepository:
    def lock(self, *, match_id, seat_id):
        # Joined match data is read, but only the seat row is locked.
        seat = (
            MatchSeat.objects.select_related("match")
            .select_for_update(of=("self",))
            .filter(pk=seat_id, match_id=match_id)
            .first()
        )
        return (
            SeatData(seat.pk, DjangoMatchRepository.to_data(seat.match), seat.price)
            if seat
            else None
        )

    def exists_for_match(self, match_id):
        return MatchSeat.objects.filter(match_id=match_id).exists()

    def replace(self, match_id, seats):
        MatchSeat.objects.filter(match_id=match_id).delete()
        MatchSeat.objects.bulk_create(
            [MatchSeat(match_id=match_id, **asdict(seat)) for seat in seats], batch_size=1000
        )

    def availability(self, match_id):
        seats = list(
            MatchSeat.objects.filter(match_id=match_id)
            .annotate(available=~Exists(Ticket.objects.filter(seat_id=OuterRef("pk"))))
            .values("id", "section", "row", "number", "price", "available")
        )
        for seat in seats:
            seat["price"] = str(seat["price"])
        return seats
