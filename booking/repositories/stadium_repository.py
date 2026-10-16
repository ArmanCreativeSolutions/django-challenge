from booking.domain.data_objects import StadiumData
from booking.models import Stadium

from .paginated_repository import PaginatedRepository


class DjangoStadiumRepository(PaginatedRepository):
    @staticmethod
    def to_data(stadium):
        return StadiumData(stadium.pk, stadium.name, stadium.address)

    def list(self, page):
        return self.page(Stadium.objects.all(), page, self.to_data)

    def get(self, stadium_id):
        stadium = Stadium.objects.filter(pk=stadium_id).first()
        return self.to_data(stadium) if stadium else None

    def create(self, *, name, address):
        return self.to_data(Stadium.objects.create(name=name, address=address))

    def get_or_create(self, *, name, address):
        stadium, _ = Stadium.objects.get_or_create(name=name, defaults={"address": address})
        return self.to_data(stadium)
