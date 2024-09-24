from rest_framework.routers import DefaultRouter
from apps.accounts.api.views.v1 import RegisterViewSet as RegisterViewSetV1


router = DefaultRouter(trailing_slash=False)
router.register("v1/register", RegisterViewSetV1, basename="register")

urlpatterns = router.urls
