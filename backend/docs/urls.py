from commons.routers import Router

from .views import ChangelogViewSet

router = Router()
router.register("changelogs", ChangelogViewSet, basename="changelog")

urlpatterns = router.urls
