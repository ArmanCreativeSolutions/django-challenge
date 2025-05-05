from django.db.models import Manager


class FilterActiveManager(Manager):
    def get_queryset(self):
        return super().get_queryset()

    def filter_active(self, **kwargs):
        return self.get_queryset().filter(active=True, **kwargs)
