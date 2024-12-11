from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    '''
    Represents users of the API. 

    is_stadium_admin: If True users are able to create stadiums and matches and ... 
                      This only can be set in django admin.
    '''
    is_stadium_admin = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=11, unique=True, null=True, blank=True)

    def __str__(self):
        return self.phone_number or self.username
