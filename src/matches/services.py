
from django.db import transaction
from matches.models import Ticket, Match, TicketFactor
from matches.exceptions import TicketReservationError, PublishMatchError, FinalizeTicketFactoryError


def publish_match(match_id):
    match_instance = Match.objects.filter(id=match_id).first()
    if match_instance is None:
        raise PublishMatchError('Match does not exist')

    if match_instance.status == Match.Status.PUBLISHED:
        raise PublishMatchError('Match is already published')

    match_instance.status = Match.Status.PUBLISHED
    match_instance.save()


def reserve_tickets(ticket_ids, user):
    '''
    This function reserves tickets for user. By locking the appropriate rows
    of DB this function prevents race conditions. 
    '''
    if not ticket_ids:
        raise TicketReservationError("No ticket IDs provided.")

    with transaction.atomic():
        # Lock chosen tickets for update
        tickets = list(
            Ticket.objects.select_for_update()
            .filter(id__in=ticket_ids)
            .filter(status=Ticket.Status.AVAILABLE)
        )

        if len(tickets) != len(ticket_ids):
            raise TicketReservationError("One or more tickets are not available.")

        match_id = tickets[0].match_instance_id
        if any(ticket.match_instance_id != match_id for ticket in tickets):
            raise TicketReservationError("Cannot buy tickets for different matches at the same time.")

        match_instance = tickets[0].match_instance
        if match_instance.status != Match.Status.PUBLISHED:
            raise TicketReservationError("Match is not published yet.")

        total_amount = sum(ticket.price for ticket in tickets)
        verification_code = TicketFactor.generate_unique_verification_code()
        ticket_factor = TicketFactor.objects.create(
            verification_code=verification_code,
            amount=total_amount,
            buyer=user,
        )

        for ticket in tickets:
            ticket.status = Ticket.Status.RESERVED_FOR_PAYMENT
            ticket.ticket_factor = ticket_factor
        Ticket.objects.bulk_update(tickets, ['status', 'ticket_factor'])

        return ticket_factor


def finailize_ticket_factor(ticket_factor_id):
    with transaction.atomic():
        ticket_factor = TicketFactor.objects.get(id=ticket_factor_id)
        if ticket_factor.status != TicketFactor.Status.WAITING_FOR_PAYMENT:
            raise FinalizeTicketFactoryError("Ticket Factor is not in the correct state.")

        ticket_factor.tickets.update(status=Ticket.Status.SOLD)
        ticket_factor.status = TicketFactor.Status.PAYED
        return ticket_factor
