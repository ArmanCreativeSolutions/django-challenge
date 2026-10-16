from booking.domain.data_objects import MatchData
from booking.models import Match

from .paginated_repository import PaginatedRepository


class DjangoMatchRepository(PaginatedRepository):
    @staticmethod
    def to_data(match):
        return MatchData(
            match.pk,
            match.stadium_id,
            match.home_team,
            match.away_team,
            match.starts_at,
            match.status,
            match.created_at,
        )

    def list(self, page, *, include_drafts):
        matches = Match.objects.all()
        if not include_drafts:
            matches = matches.filter(status=Match.Status.PUBLISHED)
        return self.page(matches, page, self.to_data)

    def get(self, match_id, *, for_update=False):
        matches = Match.objects.all()
        if for_update:
            matches = matches.select_for_update()
        match = matches.filter(pk=match_id).first()
        return self.to_data(match) if match else None

    def create(self, *, stadium, home_team, away_team, starts_at):
        return self.to_data(
            Match.objects.create(
                stadium_id=stadium, home_team=home_team, away_team=away_team, starts_at=starts_at
            )
        )

    def publish(self, match_id):
        Match.objects.filter(pk=match_id).update(status=Match.Status.PUBLISHED)
        return self.to_data(Match.objects.get(pk=match_id))

    def find_upcoming(self, *, stadium, home_team, away_team, now):
        match = Match.objects.filter(
            stadium_id=stadium,
            home_team=home_team,
            away_team=away_team,
            starts_at__gt=now,
            status=Match.Status.PUBLISHED,
        ).first()
        return self.to_data(match) if match else None
