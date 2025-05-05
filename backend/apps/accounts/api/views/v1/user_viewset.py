from rest_framework.permissions import AllowAny
from rest_framework.mixins import CreateModelMixin
from rest_framework.viewsets import GenericViewSet

from apps.accounts.models import User
from apps.accounts.api.serializers.v1 import UserSerializer


class RegisterViewSet(CreateModelMixin, GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
