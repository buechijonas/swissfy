from django.urls import path

from commons.routers import Router

from .views import LibraryViewSet, OwnPictureViewSet, OwnProfileViewSet, ProfileViewSet

router = Router()
router.register("profiles/me", OwnPictureViewSet, basename="own-pictures")
router.register("profiles/me", OwnProfileViewSet, basename="own-profile")
router.register("profiles", ProfileViewSet, basename="profiles")
router.register("", LibraryViewSet, basename="library")

urlpatterns = router.urls + [
    path("covers/<path:path>", LibraryViewSet.as_view({"get": "cover"}), name="cover"),
]
