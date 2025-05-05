from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.accounts.managers import UserManager
from apps.utils.model_mixins import TimestampedMixin, IsActiveMixin, UUIDMixin


class User(
    AbstractBaseUser, PermissionsMixin, TimestampedMixin, UUIDMixin, IsActiveMixin
):
    email = models.EmailField(unique=True)
    is_admin = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"

    objects = UserManager()
