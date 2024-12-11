from django.contrib import admin
from matches.models import Team, Ticket, Match, Stadium, Seat, SeatingArrangment


admin.site.register(Team)
admin.site.register(Ticket)
admin.site.register(Match)
admin.site.register(Stadium)
admin.site.register(Seat)
admin.site.register(SeatingArrangment)
