from functools import cached_property
from uuid import UUID

from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from booking.domain.data_objects import SeatDefinition
from shared.api.dependency_injection import DependencyMixin
from shared.api.service_pagination import ServicePagination

from .serializers import (
    BookingInputSerializer,
    ErrorSerializer,
    HealthSerializer,
    LayoutResponseSerializer,
    LayoutSerializer,
    MatchSerializer,
    SeatMapSerializer,
    StadiumSerializer,
    TicketSerializer,
)

MATCH_ID = [OpenApiParameter("id", int, OpenApiParameter.PATH)]


class ServiceViewSet(DependencyMixin, viewsets.ViewSet):
    serializer_class = None
    pagination_class = ServicePagination

    def get_serializer_class(self):
        return self.serializer_class

    def get_serializer_context(self):
        return {"request": self.request, "format": self.format_kwarg, "view": self}

    def get_serializer(self, *args, **kwargs):
        kwargs.setdefault("context", self.get_serializer_context())
        return self.get_serializer_class()(*args, **kwargs)

    @cached_property
    def paginator(self):
        return self.pagination_class() if self.pagination_class is not None else None

    @staticmethod
    def identifier(value):
        try:
            identifier = int(value)
            if identifier < 1 or identifier > 9223372036854775807:
                raise ValueError
            return identifier
        except (TypeError, ValueError) as exc:
            raise NotFound("Invalid identifier.") from exc

    def page_response(self, page):
        return self.paginator.respond(page, self.get_serializer(page.items, many=True).data)


@extend_schema_view(
    retrieve=extend_schema(parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH)]),
)
class StadiumViewSet(ServiceViewSet):
    serializer_class = StadiumSerializer

    def get_permissions(self):
        return [IsAdminUser() if self.action == "create" else AllowAny()]

    def list(self, request):
        page = self.container.catalog.list_stadiums(self.paginator.get_page_request(request))
        return self.page_response(page)

    def retrieve(self, request, pk=None):
        stadium = self.container.catalog.get_stadium(self.identifier(pk))
        return Response(self.get_serializer(stadium).data)

    @extend_schema(responses={201: StadiumSerializer})
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        stadium = self.container.catalog.create_stadium(**serializer.validated_data)
        return Response(self.get_serializer(stadium).data, status=201)


@extend_schema_view(
    retrieve=extend_schema(parameters=MATCH_ID),
    layout=extend_schema(parameters=MATCH_ID),
    publish=extend_schema(parameters=MATCH_ID),
    seats=extend_schema(parameters=MATCH_ID),
    book=extend_schema(parameters=MATCH_ID),
)
class MatchViewSet(ServiceViewSet):
    serializer_class = MatchSerializer

    def get_permissions(self):
        if self.action in {"create", "layout", "publish"}:
            return [IsAdminUser()]
        if self.action == "book":
            return [IsAuthenticated()]
        return [AllowAny()]

    def list(self, request):
        page = self.container.catalog.list_matches(
            self.paginator.get_page_request(request), include_drafts=request.user.is_staff
        )
        return self.page_response(page)

    def retrieve(self, request, pk=None):
        match = self.container.catalog.get_match(
            self.identifier(pk), include_drafts=request.user.is_staff
        )
        return Response(self.get_serializer(match).data)

    @extend_schema(responses={201: MatchSerializer})
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        match = self.container.catalog.create_match(**serializer.validated_data)
        return Response(self.get_serializer(match).data, status=201)

    @extend_schema(request=LayoutSerializer, responses={200: LayoutResponseSerializer})
    @action(detail=True, methods=["put"], serializer_class=LayoutSerializer)
    def layout(self, request, pk=None):
        serializer = LayoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = self.container.catalog.replace_layout(
            match_id=self.identifier(pk),
            seats=[SeatDefinition(**seat) for seat in serializer.validated_data["seats"]],
        )
        return Response(result)

    @extend_schema(request=None, responses={200: MatchSerializer})
    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        match = self.container.catalog.publish(match_id=self.identifier(pk))
        return Response(self.get_serializer(match).data)

    @extend_schema(responses={200: SeatMapSerializer, 503: ErrorSerializer})
    @action(detail=True, methods=["get"], pagination_class=None)
    def seats(self, request, pk=None):
        snapshot = self.container.availability.get(
            self.identifier(pk), include_drafts=request.user.is_staff
        )
        return Response(snapshot, headers={"Cache-Control": "no-store"})

    @extend_schema(
        request=BookingInputSerializer,
        responses={
            201: TicketSerializer,
            400: ErrorSerializer,
            409: ErrorSerializer,
            503: ErrorSerializer,
        },
        parameters=[
            OpenApiParameter(
                "Idempotency-Key",
                str,
                OpenApiParameter.HEADER,
                required=True,
                description="1–128 visible ASCII characters, scoped to the authenticated user.",
            ),
            OpenApiParameter("Idempotency-Replayed", bool, OpenApiParameter.HEADER, response=[201]),
        ],
        description=(
            "Purchase one seat. Reusing a successful key and the same match/seat replays the "
            "original 201 response. A different payload returns 409. Failed requests do not "
            "consume the key. Send the same key after a timeout or 503."
        ),
    )
    @action(
        detail=True, methods=["post"], url_path="bookings", serializer_class=BookingInputSerializer
    )
    def book(self, request, pk=None):
        serializer = BookingInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        match = self.container.catalog.get_match(
            self.identifier(pk), include_drafts=request.user.is_staff
        )
        result = self.container.booking.book(
            user_id=request.user.pk,
            match_id=match.id,
            seat_id=serializer.validated_data["seat_id"],
            idempotency_key=request.headers.get("Idempotency-Key", ""),
        )
        return Response(
            result.response,
            status=result.status_code,
            headers={
                "Idempotency-Replayed": str(result.replayed).lower(),
                "Cache-Control": "no-store",
            },
        )


@extend_schema_view(
    retrieve=extend_schema(parameters=[OpenApiParameter("id", UUID, OpenApiParameter.PATH)]),
)
class TicketViewSet(ServiceViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request):
        page = self.container.ticket_reader.list(
            user_id=request.user.pk, page=self.paginator.get_page_request(request)
        )
        return self.page_response(page)

    def retrieve(self, request, pk=None):
        try:
            ticket_id = UUID(pk)
        except (TypeError, ValueError, AttributeError) as exc:
            raise NotFound("No such ticket.") from exc
        ticket = self.container.ticket_reader.get(user_id=request.user.pk, ticket_id=ticket_id)
        return Response(self.get_serializer(ticket).data)


class HealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(responses=HealthSerializer)
    def get(self, request):
        return Response({"status": "ok"})
