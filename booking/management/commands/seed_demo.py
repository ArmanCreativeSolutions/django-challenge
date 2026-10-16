from django.core.management.base import BaseCommand

from volleyball_ticketing.dependency_container import ApplicationContainer


class Command(BaseCommand):
    help = "Create one published demonstration match with 100 seats (no user credentials)."

    def handle(self, *args, **options):
        match = ApplicationContainer().demo.seed()
        self.stdout.write(self.style.SUCCESS(f"Demo match: /api/matches/{match.id}/"))
