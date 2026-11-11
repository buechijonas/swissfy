from commons.routers import Router

from .administration import AdminUserViewSet, RoleViewSet

router = Router()
router.register("roles", RoleViewSet, basename="admin-roles")
router.register("users", AdminUserViewSet, basename="admin-users")

urlpatterns = router.urls
