from commons.routers import Router

from .internal import InternalProfileViewSet

router = Router()
router.register("profiles", InternalProfileViewSet, basename="internal-profiles")

urlpatterns = router.urls
