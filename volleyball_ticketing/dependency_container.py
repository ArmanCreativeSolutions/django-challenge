from django.conf import settings

from accounts.infrastructure.authentication_adapters import (
    DjangoCredentialVerifier,
    DjangoRegistrationPolicy,
)
from accounts.repositories.buyer_repository import DjangoBuyerRepository
from accounts.repositories.token_repository import DjangoTokenRepository
from accounts.repositories.user_repository import DjangoUserRepository
from accounts.services.authentication_service import AuthenticationService
from booking.domain.contracts import SeatMapCache
from booking.infrastructure.redis_seat_map_cache import RedisClientProvider, RedisSeatMapCache
from booking.repositories.idempotency_repository import DjangoReplayRepository
from booking.repositories.match_repository import DjangoMatchRepository
from booking.repositories.seat_repository import DjangoSeatRepository
from booking.repositories.stadium_repository import DjangoStadiumRepository
from booking.repositories.ticket_repository import DjangoTicketRepository
from booking.services.availability_service import AvailabilityService
from booking.services.booking_service import BookingService
from booking.services.catalog_service import CatalogService
from booking.services.demo_data_service import DemoDataService
from booking.services.ticket_service import TicketService
from shared.contracts import Clock, TransactionManager
from shared.infrastructure.system_clock import SystemClock
from shared.infrastructure.transaction_manager import DjangoTransactionManager


class ApplicationContainer:
    def __init__(
        self,
        *,
        seat_maps: SeatMapCache | None = None,
        clock: Clock | None = None,
        transactions: TransactionManager | None = None,
    ):
        self.clock = clock if clock is not None else SystemClock()
        self.transactions = transactions if transactions is not None else DjangoTransactionManager()
        self.seat_maps = (
            seat_maps
            if seat_maps is not None
            else RedisSeatMapCache(
                client=RedisClientProvider.get(settings.REDIS_URL),
                ttl=settings.SEAT_CACHE_TTL,
                lock_ttl=settings.SEAT_CACHE_LOCK_TTL,
            )
        )
        self.buyers = DjangoBuyerRepository()
        self.stadiums = DjangoStadiumRepository()
        self.matches = DjangoMatchRepository()
        self.seats = DjangoSeatRepository()
        self.tickets = DjangoTicketRepository()
        self.replays = DjangoReplayRepository()
        self.users = DjangoUserRepository()
        self.tokens = DjangoTokenRepository()
        self.catalog = CatalogService(
            stadiums=self.stadiums,
            matches=self.matches,
            seats=self.seats,
            transactions=self.transactions,
            cache=self.seat_maps,
            clock=self.clock,
            max_seats=settings.SEAT_MAP_MAX_SIZE,
        )
        self.booking = BookingService(
            buyers=self.buyers,
            seats=self.seats,
            tickets=self.tickets,
            replays=self.replays,
            transactions=self.transactions,
            cache=self.seat_maps,
            clock=self.clock,
        )
        self.availability = AvailabilityService(
            seats=self.seats,
            cache=self.seat_maps,
            catalog=self.catalog,
            clock=self.clock,
            ttl=settings.SEAT_CACHE_TTL,
        )
        self.ticket_reader = TicketService(tickets=self.tickets)
        self.auth = AuthenticationService(
            users=self.users,
            tokens=self.tokens,
            credentials=DjangoCredentialVerifier(),
            registration=DjangoRegistrationPolicy(),
            transactions=self.transactions,
        )
        self.demo = DemoDataService(
            catalog=self.catalog,
            stadiums=self.stadiums,
            matches=self.matches,
            transactions=self.transactions,
            clock=self.clock,
        )
