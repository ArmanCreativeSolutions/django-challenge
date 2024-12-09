from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    is_stadium_admin = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=11, unique=True, null=True, blank=True)

    def __str__(self):
        return self.phone_number