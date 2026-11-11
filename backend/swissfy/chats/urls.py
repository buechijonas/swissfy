from commons.routers import Router

from .views import ChatViewSet, ConversationViewSet

router = Router()
router.register("", ChatViewSet, basename="chats")
router.register("", ConversationViewSet, basename="conversations")

urlpatterns = router.urls
