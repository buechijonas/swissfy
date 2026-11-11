from commons.routers import Router
from swissfy.social.views import StoryViewerViewSet

from .views.albums import (
    AlbumEntryCollectionViewSet,
    AlbumEntryViewSet,
    AlbumViewSet,
    UserAlbumViewSet,
)
from .views.collections import ContactGroupViewSet, SavedFolderViewSet
from .views.comments import CommentReplyViewSet, CommentViewSet, PostCommentViewSet
from .views.hashtags import HashtagPostViewSet, HashtagViewSet
from .views.media import PostMediaViewSet
from .views.posts import PostViewSet
from .views.stories import StoryViewSet
from .views.users import UserPostViewSet

router = Router()
router.register("posts/hashtags/<str:name>/posts", HashtagPostViewSet, basename="hashtag-posts")
router.register("posts/hashtags", HashtagViewSet, basename="hashtags")
router.register("posts/folders", SavedFolderViewSet, basename="saved-folders")
router.register("posts/groups", ContactGroupViewSet, basename="contact-groups")
router.register("posts/users/<str:username>/albums", UserAlbumViewSet, basename="user-albums")
router.register("posts/users/<str:username>", UserPostViewSet, basename="user-posts")
router.register("posts/<uuid:uuid>/comments", PostCommentViewSet, basename="post-comments")
router.register("posts", PostViewSet, basename="posts")
router.register("posts", PostMediaViewSet, basename="post-media")
router.register("albums/<uuid:uuid>/entries", AlbumEntryCollectionViewSet, basename="album-entries")
router.register("albums", AlbumViewSet, basename="albums")
router.register("album-entries", AlbumEntryViewSet, basename="album-entry")
router.register("stories/<uuid:uuid>/viewers", StoryViewerViewSet, basename="story-viewers")
router.register("stories", StoryViewSet, basename="stories")
router.register("comments/<uuid:uuid>/replies", CommentReplyViewSet, basename="comment-replies")
router.register("comments", CommentViewSet, basename="comments")

urlpatterns = router.urls
