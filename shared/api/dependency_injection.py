from functools import cached_property

from volleyball_ticketing.dependency_container import ApplicationContainer


class DependencyMixin:
    dependencies = None

    @cached_property
    def container(self):
        return self.dependencies if self.dependencies is not None else ApplicationContainer()
