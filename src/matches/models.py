import secrets
from django.db import models
from users.models import CustomUser


class Stadium(models.Model):
    title = models.CharField(max_length=100)
    address = models.TextField()
    lat = models.FloatField()
    long = models.FloatField()

    created_by = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class SeatingArrangment(models.Model):
    '''
    Represents seating arrangement of a stadium. This model enables a stadium
    to have multiple seating arrangements and choosing the proper one for each 
    match.
    '''
    stadium = models.ForeignKey(Stadium, on_delete=models.PROTECT)


class Seat(models.Model):
    '''
    Represents a seat in a seating arrangement of a stadium

    column: Seat real world identifier.
    row: Seat real world identifier.
    section: Seat real world identifier.

    pos_x, pos_y: Coordination of seat in a visual representation.
    seating_arrangment: The seating arrangement the seat belongs to.

    '''

    column = models.CharField(max_length=5)
    row = models.CharField(max_length=5)
    section = models.CharField(max_length=5, null=True, blank=True)

    pos_x = models.IntegerField()
    pos_y = models.IntegerField()

    seating_arrangment = models.ForeignKey(
        SeatingArrangment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='seats',
    )

    def name(self):
        name = ''
        if self.section is not None:
            name += f'sec: {self.section}, '
        
        name += f'row: {self.row}, column: {self.column}'
        return name


class Team(models.Model):
    name = models.CharField(max_length=100)


class Match(models.Model):
    '''
    Represents a match between team_a and team_b on match_datetime.

    status: Having status enables being able to create matches in multiple stages and not
            publishing a match before it is intended to.

    seating_arrangement: matches tickets are created based on the seating arrangement.
    '''
    class Status(models.IntegerChoices):
        DRAFT = 0, 'Draft'
        PUBLISHED = 1, 'Published',

    team_a = models.ForeignKey(Team, on_delete=models.PROTECT, related_name='matches_as_team_a')
    team_b = models.ForeignKey(Team, on_delete=models.PROTECT, related_name='matches_as_team_b')

    seating_arrangement = models.ForeignKey(SeatingArrangment, on_delete=models.PROTECT)

    match_datetime = models.DateTimeField()
    status = models.IntegerField(choices=Status.choices, default=Status.DRAFT)


class TicketFactor(models.Model):
    '''
    Represents bought tickets or reservation for buying tickets before payment.

    verification_code: A human readable code for verifying tickets purchase
    amount: Total amount of required payment
    created_at: Important when we want to take unpayed ticket factors(in state of WAITING_FOR_PAYMENT)
                to state of CANCEL.
    '''
    class Status(models.IntegerChoices):
        WAITING_FOR_PAYMENT = 0, 'Waiting for payment'
        PAYED = 1, 'Payed'
        CANCELED = 2, 'Canceled'

    # A human readable code for verifying tickets purchase
    verification_code = models.CharField(max_length=10, unique=True)
    amount = models.PositiveIntegerField()
    status = models.IntegerField(choices=Status.choices, default=Status.WAITING_FOR_PAYMENT)
    created_at = models.DateTimeField(auto_now_add=True)
    buyer = models.ForeignKey(CustomUser, on_delete=models.PROTECT)

    @classmethod
    def generate_unique_verification_code(cls):
        while True:
            code = secrets.randbelow(10**10)
            code_str = f"{code:010}"
            if not cls.objects.filter(verification_code=code_str).exists():
                return code_str


class Ticket(models.Model):
    '''
        Tickets are the connection between seat and match holding extra data like price and team
        they are defined for each seat of the seating arrangment for match enabling dynamic 
        price and team location.

        team: represents which team the seat belongs to. Can be null meaning the seat is neutral
        price: price of the ticket. 
    '''
    class Status(models.IntegerChoices):
        AVAILABLE = 0, 'Available'
        RESERVED_FOR_PAYMENT = 1, 'Reserved for payment'
        SOLD = 2, 'Sold'

    match_instance = models.ForeignKey(Match, on_delete=models.PROTECT, related_name='tickets')
    seat = models.ForeignKey(Seat, on_delete=models.PROTECT)
    team = models.ForeignKey(Team, null=True, on_delete=models.SET_NULL)
    price = models.PositiveIntegerField()
    status = models.IntegerField(choices=Status.choices, default=Status.AVAILABLE)

    ticket_factor = models.ForeignKey(
        TicketFactor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets'
    )
