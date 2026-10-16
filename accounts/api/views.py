from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from shared.api.dependency_injection import DependencyMixin

from .serializers import AuthResponseSerializer, LoginSerializer, SignupSerializer


class PublicAuthView(DependencyMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def get_authenticate_header(self, request):
        return "Token"


class SignupView(PublicAuthView):
    @extend_schema(request=SignupSerializer, responses={201: AuthResponseSerializer})
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = self.container.auth.signup(**serializer.validated_data)
        return Response(AuthResponseSerializer(result).data, status=201)


class LoginView(PublicAuthView):
    @extend_schema(request=LoginSerializer, responses={200: AuthResponseSerializer})
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = self.container.auth.login(**serializer.validated_data)
        return Response(AuthResponseSerializer(result).data)


class LogoutView(DependencyMixin, APIView):
    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        self.container.auth.logout(token=request.auth.key)
        return Response(status=204)
