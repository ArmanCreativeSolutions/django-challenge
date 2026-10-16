from datetime import timedelta
from decimal import Decimal

from booking.domain.contracts import MatchRepository, StadiumRepository
from booking.domain.data_objects import SeatDefinition
from shared.contracts import Clock, TransactionManager

from .catalog_service import CatalogService


class DemoDataService:
    def __init__(
        self,
        *,
        catalog: CatalogService,
        stadiums: StadiumRepository,
        matches: MatchRepository,
        transactions: TransactionManager,
        clock: Clock,
    ):
        self.catalog = catalog
        self.stadiums = stadiums
        self.matches = matches
        self.transactions = transactions
        self.clock = clock

    def seed(self):
        with self.transactions.atomic():
            stadium = self.stadiums.get_or_create(name="Demo Volleyball Arena", address="Tehran")
            match = self.matches.find_upcoming(
                stadium=stadium.id,
                home_team="Demo Falcons",
                away_team="Demo Waves",
                now=self.clock.now(),
            )
            if match is not None:
                return match
            match = self.catalog.create_match(
                stadium=stadium.id,
                home_team="Demo Falcons",
                away_team="Demo Waves",
                starts_at=self.clock.now() + timedelta(days=7),
            )
            self.catalog.replace_layout(
                match_id=match.id,
                seats=[
                    SeatDefinition("A", str(row), number, Decimal("25.00"))
                    for row in range(1, 6)
                    for number in range(1, 21)
                ],
            )
            return self.catalog.publish(match_id=match.id)
