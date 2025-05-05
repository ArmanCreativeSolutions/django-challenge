import datetime
from datetime import timedelta

import logging

from rest_framework.exceptions import APIException

from apps.utils.enums import MESSAGES
from apps.utils.helpers import CacheManager

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    RateLimiter is a helper class to use it in a middleware or views to control users requests limitation.
    :example: limiter = RateLimiter('127.0.0.1', 'register')
    """
    def __init__(self, ip_or_username: str, level: str):
        self._level = level
        self._cache_manager = CacheManager(f"{level}_invalid_attempt_{ip_or_username}")

    @property
    def level(self) -> str:
        """Level of request, like register, login, seat reservation, etc..."""
        return self._level

    @property
    def is_locked(self) -> bool:
        try:
            if self._cache_manager.value and self._cache_manager.value.get("lockout_start"):
                lockout_start = datetime.datetime.strptime(
                    self._cache_manager.value.get("lockout_start"),
                    '%Y-%m-%d %H:%M:%S'
                )
                locked_out = lockout_start >= datetime.datetime.now() - timedelta(minutes=-60)
                if not locked_out:
                    self._cache_manager.delete()
                    return False
                else:
                    return True
            else:
                return False
        except Exception as e:
            logger.error(e)
            return False

    def set_new_timestamp(self):
        if not self.is_locked:
            lockout_timestamp = None
            invalid_attempt_timestamps = (
                self._cache_manager.value.get(
                    "invalid_attempt_timestamps") if self._cache_manager.value else []
            )
            invalid_attempt_timestamps = [
                timestamp_item
                for timestamp_item in invalid_attempt_timestamps
                if timestamp_item > (datetime.datetime.now() - timedelta(minutes=-60)).timestamp()
            ]
            invalid_attempt_timestamps.append(datetime.datetime.now().timestamp())
            if len(invalid_attempt_timestamps) == 3:
                lockout_timestamp = datetime.datetime.now().timestamp()

            self._cache_manager.value = {
                "lockout_start": lockout_timestamp,
                "invalid_attempt_timestamps": invalid_attempt_timestamps,
            }

    def check_if_limited(self, msg: str, code: int) -> None:
        """ Checks if the IP address is blocked """
        if not self.is_locked:
            self.set_new_timestamp()
            raise APIException(msg, code)
        else:
            raise APIException(MESSAGES.ALERTS.YOUR_IP_ADDRESS_LOCKED, 403)
