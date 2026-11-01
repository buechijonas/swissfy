from django.urls import path

from social import views as social_views

from .views.albums import AlbumEntryViewSet, AlbumViewSet
from .views.collections import ContactGroupViewSet, SavedFolderViewSet
from .views.comments import CommentReplyViewSet, CommentViewSet, PostCommentViewSet
from .views.hashtags import HashtagPostViewSet, HashtagViewSet
from .views.media import PostMediaViewSet
from .views.posts import PostViewSet
from .views.stories import StoryViewSet
from .views.users import UserPostViewSet

urlpatterns = [
    path("posts/", PostViewSet.as_view({"get": "list", "post": "create"}), name="feed"),
    path("posts/global/", PostViewSet.as_view({"get": "global_feed"}), name="global-feed"),
    path("posts/quota/", PostViewSet.as_view({"get": "quota"}), name="post-quota"),
    path("posts/reels/", PostViewSet.as_view({"get": "reels"}), name="reel-feed"),
    path("posts/hashtags/", HashtagViewSet.as_view({"get": "list"}), name="hashtags"),
    path("posts/hashtags/<str:name>/", HashtagViewSet.as_view({"get": "retrieve"}), name="hashtag"),
    path(
        "posts/hashtags/<str:name>/follow/",
        HashtagViewSet.as_view({"put": "follow", "delete": "unfollow"}),
        name="hashtag-follow",
    ),
    path(
        "posts/hashtags/<str:name>/posts/",
        HashtagPostViewSet.as_view({"get": "list"}),
        name="hashtag-posts",
    ),
    path("posts/saved/", PostViewSet.as_view({"get": "saved"}), name="saved-posts"),
    path(
        "posts/folders/",
        SavedFolderViewSet.as_view({"get": "list", "post": "create"}),
        name="saved-folders",
    ),
    path(
        "posts/folders/<int:pk>/",
        SavedFolderViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="saved-folder",
    ),
    path(
        "posts/groups/",
        ContactGroupViewSet.as_view({"get": "list", "post": "create"}),
        name="contact-groups",
    ),
    path(
        "posts/groups/<int:pk>/",
        ContactGroupViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="contact-group",
    ),
    path(
        "posts/users/<str:username>/",
        UserPostViewSet.as_view({"get": "list"}),
        name="user-posts",
    ),
    path(
        "posts/users/<str:username>/albums/",
        AlbumViewSet.as_view({"get": "list"}),
        name="user-albums",
    ),
    path(
        "posts/users/<str:username>/activities/",
        UserPostViewSet.as_view({"get": "activities"}),
        name="user-activities",
    ),
    path(
        "posts/<uuid:uuid>/",
        PostViewSet.as_view({"get": "retrieve", "patch": "update", "delete": "destroy"}),
        name="post",
    ),
    path(
        "posts/<uuid:uuid>/images/<int:position>/",
        PostMediaViewSet.as_view({"get": "image"}),
        name="post-image",
    ),
    path("posts/<uuid:uuid>/video/", PostMediaViewSet.as_view({"get": "video"}), name="post-video"),
    path(
        "posts/<uuid:uuid>/thumbnail/",
        PostMediaViewSet.as_view({"get": "thumbnail"}),
        name="post-thumbnail",
    ),
    path(
        "posts/<uuid:uuid>/like/",
        PostViewSet.as_view({"post": "like", "delete": "unlike"}),
        name="post-like",
    ),
    path(
        "posts/<uuid:uuid>/repost/",
        PostViewSet.as_view({"post": "repost", "delete": "unrepost"}),
        name="post-repost",
    ),
    path(
        "posts/<uuid:uuid>/save/",
        PostViewSet.as_view({"put": "save", "delete": "unsave"}),
        name="post-save",
    ),
    path(
        "posts/<uuid:uuid>/comments/",
        PostCommentViewSet.as_view({"get": "list", "post": "create"}),
        name="post-comments",
    ),
    path("albums/", AlbumViewSet.as_view({"post": "create"}), name="albums"),
    path("albums/order/", AlbumViewSet.as_view({"put": "order"}), name="album-order"),
    path(
        "albums/<uuid:uuid>/",
        AlbumViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}),
        name="album",
    ),
    path(
        "albums/<uuid:uuid>/entries/",
        AlbumEntryViewSet.as_view({"post": "create"}),
        name="album-entries",
    ),
    path(
        "album-entries/<uuid:uuid>/",
        AlbumEntryViewSet.as_view({"patch": "partial_update", "delete": "destroy"}),
        name="album-entry",
    ),
    path("stories/", StoryViewSet.as_view({"post": "create"}), name="stories"),
    path("stories/<uuid:uuid>/", StoryViewSet.as_view({"delete": "destroy"}), name="story"),
    path("stories/<uuid:uuid>/image/", StoryViewSet.as_view({"get": "image"}), name="story-image"),
    path(
        "stories/<uuid:uuid>/like/",
        StoryViewSet.as_view({"post": "like", "delete": "unlike"}),
        name="story-like",
    ),
    path("stories/<uuid:uuid>/view/", StoryViewSet.as_view({"post": "view"}), name="story-view"),
    path(
        "stories/<uuid:uuid>/viewers/",
        social_views.StoryViewerListView.as_view(),
        name="story-viewers",
    ),
    path(
        "comments/<uuid:uuid>/",
        CommentViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="comment",
    ),
    path(
        "comments/<uuid:uuid>/vote/", CommentViewSet.as_view({"put": "vote"}), name="comment-vote"
    ),
    path(
        "comments/<uuid:uuid>/replies/",
        CommentReplyViewSet.as_view({"get": "list", "post": "create"}),
        name="comment-replies",
    ),
]
