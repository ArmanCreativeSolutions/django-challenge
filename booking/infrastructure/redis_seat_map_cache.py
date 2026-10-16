import json
import logging
from contextlib import contextmanager
from functools import lru_cache

from redis import Redis
from redis.backoff import NoBackoff
from redis.exceptions import RedisError
from redis.retry import Retry

from shared.application_errors import ServiceUnavailableError

logger = logging.getLogger(__name__)


class RedisClientProvider:
    @staticmethod
    @lru_cache(maxsize=8)
    def get(url: str):
        return Redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=0.3,
            socket_timeout=0.3,
            max_connections=30,
            retry=Retry(NoBackoff(), 0),
        )


class RedisSeatMapCache:
    def __init__(self, *, client, ttl: int, lock_ttl: int, prefix="ticketing:v1:match"):
        self.client = client
        self.ttl = ttl
        self.lock_ttl = lock_ttl
        self.prefix = prefix

    def key(self, match_id: int):
        return f"{self.prefix}:{match_id}:seats"

    def get(self, match_id: int):
        try:
            cached = self.client.get(self.key(match_id))
            if cached is None:
                return None
            snapshot = json.loads(cached)
            if not isinstance(snapshot, dict) or snapshot.get("match_id") != match_id:
                raise ValueError("Invalid availability snapshot")
            return snapshot
        except (RedisError, ValueError) as exc:
            raise ServiceUnavailableError("Seat availability is temporarily unavailable.") from exc

    def set(self, match_id: int, snapshot: dict):
        try:
            self.client.set(self.key(match_id), json.dumps(snapshot), ex=self.ttl)
        except RedisError as exc:
            raise ServiceUnavailableError("Seat availability is temporarily unavailable.") from exc

    @contextmanager
    def filling(self, match_id: int):
        lock = self.client.lock(f"{self.key(match_id)}:fill", timeout=self.lock_ttl)
        try:
            acquired = lock.acquire(blocking=False)
        except RedisError as exc:
            raise ServiceUnavailableError("Seat availability is temporarily unavailable.") from exc
        if not acquired:
            raise ServiceUnavailableError("Seat availability is refreshing. Retry shortly.")
        try:
            yield
        finally:
            try:
                lock.release()
            except RedisError:
                logger.warning("Seat-map fill lock release failed", exc_info=True)

    def invalidate(self, match_id: int):
        try:
            self.client.delete(self.key(match_id))
        except RedisError:
            # A failed cache callback cannot change a committed sale into an HTTP failure.
            logger.warning("Seat-map invalidation failed for match %s", match_id, exc_info=True)
