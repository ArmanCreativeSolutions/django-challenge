from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from matches.serializers import (
    StadiumSerializer,
    SeatingArrangementSerializer,
    MatchCreateSerializer,
    TicketFactorSerializer,
)
from matches.exceptions import TicketReservationError, PublishMatchError, FinalizeTicketFactoryError
from matches.services import reserve_tickets, publish_match, finailize_ticket_factor
from matches.models import TicketFactor
from users.permissions import IsStadiumAdmin


class StadiumCreateView(APIView):
    permission_classes = [IsStadiumAdmin]

    def post(self, request):
        serializer = StadiumSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SeatingArrangementCreateView(APIView):
    permission_classes = [IsStadiumAdmin]

    def post(self, request):
        serializer = SeatingArrangementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MatchCreateView(APIView):
    permission_classes = [IsStadiumAdmin]

    def post(self, request):
        serializer = MatchCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MatchPublishView(APIView):
    permission_classes = [IsStadiumAdmin]

    def patch(self, request, match_id):
        try:
            publish_match(match_id)
            return Response({'message': 'Match published successfully'}, status=status.HTTP_200_OK)
        except PublishMatchError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ReserveTicketsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ticket_ids = request.data.get('ticket_ids', [])
        try:
            ticket_factor = reserve_tickets(ticket_ids, request.user)
            serializer = TicketFactorSerializer(ticket_factor)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except TicketReservationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FinalizeTicketFactorView(APIView):
    permission_classes = [IsAuthenticated]

    # dummy api to finalize ticket_factor(should be done in payment callback api)
    def post(self, requset, ticket_factor_id):
        try:
            ticket_factor = finailize_ticket_factor(ticket_factor_id)
            serializer = TicketFactorSerializer(ticket_factor)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except TicketFactor.DoesNotExist:
            Response({'error': f'Ticket factor ({ticket_factor_id}) not found'}, status=status.HTTP_404_NOT_FOUND)
        except FinalizeTicketFactoryError as e:
            Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
