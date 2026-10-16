from uuid import UUID

from booking.domain.contracts import TicketRepository
from shared.application_errors import NotFoundError
from shared.contracts import PageRequest


class TicketService:
    def __init__(self, *, tickets: TicketRepository):
        self.tickets = tickets

    def list(self, *, user_id: int, page: PageRequest):
        return self.tickets.list_for_buyer(user_id, page)

    def get(self, *, user_id: int, ticket_id: UUID):
        ticket = self.tickets.get_for_buyer(user_id, ticket_id)
        if ticket is None:
            raise NotFoundError("ticket_not_found", "No such ticket.")
        return ticket
