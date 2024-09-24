from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.managers import UserManager
from apps.utils.model_mixins import TimestampedMixin, IsActiveMixin, UUIDMixin


class User(
    AbstractBaseUser, PermissionsMixin, TimestampedMixin, UUIDMixin, IsActiveMixin
):
    email = models.EmailField(_("email address"), unique=True)

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"

    objects = UserManager()
