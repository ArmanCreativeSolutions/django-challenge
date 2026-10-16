from booking.domain.contracts import SeatMapCache, SeatRepository
from shared.contracts import Clock

from .catalog_service import CatalogService


class AvailabilityService:
    def __init__(
        self,
        *,
        seats: SeatRepository,
        cache: SeatMapCache,
        catalog: CatalogService,
        clock: Clock,
        ttl: int,
    ):
        self.seats = seats
        self.cache = cache
        self.catalog = catalog
        self.clock = clock
        self.ttl = ttl

    def get(self, match_id: int, *, include_drafts: bool = False):
        match = self.catalog.get_match(match_id, include_drafts=include_drafts)
        return {**self.snapshot(match_id), "sales_open": match.sales_open(self.clock.now())}

    def snapshot(self, match_id: int):
        cached = self.cache.get(match_id)
        if cached is not None:
            return cached
        # No database fallback: the cache adapter raises on outage or fill contention.
        with self.cache.filling(match_id):
            cached = self.cache.get(match_id)
            if cached is not None:
                return cached
            snapshot = self.build_snapshot(match_id)
            self.cache.set(match_id, snapshot)
            return snapshot

    def build_snapshot(self, match_id: int):
        seats = self.seats.availability(match_id)
        return {
            "match_id": match_id,
            "generated_at": self.clock.now().isoformat(),
            "cache_ttl_seconds": self.ttl,
            "available_count": sum(seat["available"] for seat in seats),
            "seats": seats,
        }
