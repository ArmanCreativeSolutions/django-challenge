from django.db import models


class IsActiveMixin(models.Model):
    is_active = models.BooleanField(default=False)

    class Meta:
        abstract = True
