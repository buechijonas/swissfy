from commons.routers import Router

from .views import NotificationViewSet

router = Router()
router.register("", NotificationViewSet, basename="notifications")

urlpatterns = router.urls
