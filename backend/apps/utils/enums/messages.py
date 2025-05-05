from enum import Enum

from django.utils.translation import gettext_lazy as _


class MESSAGES(Enum):
    class ALERTS(Enum):
        YOUR_IP_ADDRESS_LOCKED = _('Your IP Address Locked')

        def __str__(self):
            return self.value
