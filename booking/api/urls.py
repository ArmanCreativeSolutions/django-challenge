from rest_framework.routers import DefaultRouter

from .views import MatchViewSet, StadiumViewSet, TicketViewSet

router = DefaultRouter()
router.register("stadiums", StadiumViewSet, basename="stadium")
router.register("matches", MatchViewSet, basename="match")
router.register("tickets", TicketViewSet, basename="ticket")
urlpatterns = router.urls
