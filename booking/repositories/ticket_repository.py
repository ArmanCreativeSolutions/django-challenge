from booking.domain.data_objects import TicketData
from booking.models import Ticket

from .paginated_repository import PaginatedRepository


class DjangoTicketRepository(PaginatedRepository):
    @staticmethod
    def to_data(ticket):
        return TicketData(
            ticket.pk, ticket.match_id, ticket.seat_id, ticket.price, ticket.created_at
        )

    def exists_for_buyer(self, *, user_id, match_id):
        return Ticket.objects.filter(user_id=user_id, match_id=match_id).exists()

    def exists_for_seat(self, seat_id):
        return Ticket.objects.filter(seat_id=seat_id).exists()

    def create(self, *, user_id, match_id, seat_id, price):
        return self.to_data(
            Ticket.objects.create(user_id=user_id, match_id=match_id, seat_id=seat_id, price=price)
        )

    def list_for_buyer(self, user_id, page):
        return self.page(Ticket.objects.filter(user_id=user_id), page, self.to_data)

    def get_for_buyer(self, user_id, ticket_id):
        ticket = Ticket.objects.filter(user_id=user_id, pk=ticket_id).first()
        return self.to_data(ticket) if ticket else None
