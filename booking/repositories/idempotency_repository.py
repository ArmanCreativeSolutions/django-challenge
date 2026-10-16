from booking.domain.data_objects import ReplayData
from booking.models import IdempotencyRecord


class DjangoReplayRepository:
    def get(self, user_id, key):
        record = IdempotencyRecord.objects.filter(user_id=user_id, key=key).first()
        return (
            ReplayData(record.fingerprint, record.response, record.status_code) if record else None
        )

    def create(self, user_id, key, record):
        IdempotencyRecord.objects.create(
            user_id=user_id,
            key=key,
            fingerprint=record.fingerprint,
            response=record.response,
            status_code=record.status_code,
        )
