from commons.routers import Router

from .views import AchievementViewSet

router = Router()
router.register("profiles", AchievementViewSet, basename="profile-achievements")

urlpatterns = router.urls
