from contextlib import contextmanager

from django.db import IntegrityError, OperationalError, transaction

from shared.application_errors import PersistenceConflict, ServiceUnavailableError


class CommitCallback:
    def __init__(self, callback):
        self.callback = callback

    def run(self):
        self.callback()


class DjangoTransactionManager:
    @contextmanager
    def atomic(self):
        try:
            with transaction.atomic():
                yield
        except IntegrityError as exc:
            # Translation happens AFTER rollback, so callers can query safely.
            raise PersistenceConflict("A database constraint rejected the write.") from exc
        except OperationalError as exc:
            raise ServiceUnavailableError() from exc

    def after_commit(self, callback):
        transaction.on_commit(CommitCallback(callback).run, robust=True)
