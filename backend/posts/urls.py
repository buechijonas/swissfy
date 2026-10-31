from django.urls import path

from social import views as social_views

from .views import albums, collections, comments, feeds, hashtags, media, posts, stories

urlpatterns = [
    path("posts/", feeds.FeedView.as_view(), name="feed"),
    path("posts/global/", feeds.GlobalFeedView.as_view(), name="global-feed"),
    path("posts/quota/", posts.PostQuotaView.as_view(), name="post-quota"),
    path("posts/reels/", feeds.ReelFeedView.as_view(), name="reel-feed"),
    path("posts/hashtags/", hashtags.HashtagSearchView.as_view(), name="hashtags"),
    path("posts/hashtags/<str:name>/", hashtags.HashtagDetailView.as_view(), name="hashtag"),
    path(
        "posts/hashtags/<str:name>/follow/",
        hashtags.HashtagFollowView.as_view(),
        name="hashtag-follow",
    ),
    path(
        "posts/hashtags/<str:name>/posts/",
        hashtags.HashtagPostListView.as_view(),
        name="hashtag-posts",
    ),
    path("posts/saved/", feeds.SavedListView.as_view(), name="saved-posts"),
    path("posts/folders/", collections.FolderListView.as_view(), name="saved-folders"),
    path("posts/folders/<int:pk>/", collections.FolderDetailView.as_view(), name="saved-folder"),
    path("posts/groups/", collections.GroupListView.as_view(), name="contact-groups"),
    path("posts/groups/<int:pk>/", collections.GroupDetailView.as_view(), name="contact-group"),
    path("posts/users/<str:username>/", feeds.UserPostListView.as_view(), name="user-posts"),
    path(
        "posts/users/<str:username>/albums/",
        albums.UserAlbumListView.as_view(),
        name="user-albums",
    ),
    path(
        "posts/users/<str:username>/activities/",
        feeds.ActivityView.as_view(),
        name="user-activities",
    ),
    path("posts/<uuid:uuid>/", posts.PostDetailView.as_view(), name="post"),
    path(
        "posts/<uuid:uuid>/images/<int:position>/",
        media.PostImageView.as_view(),
        name="post-image",
    ),
    path("posts/<uuid:uuid>/video/", media.PostVideoView.as_view(), name="post-video"),
    path("posts/<uuid:uuid>/thumbnail/", media.PostThumbnailView.as_view(), name="post-thumbnail"),
    path("posts/<uuid:uuid>/like/", posts.LikeView.as_view(), name="post-like"),
    path("posts/<uuid:uuid>/repost/", posts.RepostView.as_view(), name="post-repost"),
    path("posts/<uuid:uuid>/save/", posts.SaveView.as_view(), name="post-save"),
    path("posts/<uuid:uuid>/comments/", comments.CommentListView.as_view(), name="post-comments"),
    path("albums/", albums.AlbumListView.as_view(), name="albums"),
    path("albums/order/", albums.AlbumOrderView.as_view(), name="album-order"),
    path("albums/<uuid:uuid>/", albums.AlbumDetailView.as_view(), name="album"),
    path(
        "albums/<uuid:uuid>/entries/",
        albums.AlbumEntryListView.as_view(),
        name="album-entries",
    ),
    path(
        "album-entries/<uuid:uuid>/",
        albums.AlbumEntryDetailView.as_view(),
        name="album-entry",
    ),
    path("stories/", stories.StoryCreateView.as_view(), name="stories"),
    path("stories/<uuid:uuid>/", stories.StoryDetailView.as_view(), name="story"),
    path("stories/<uuid:uuid>/image/", stories.StoryImageView.as_view(), name="story-image"),
    path("stories/<uuid:uuid>/like/", stories.StoryLikeView.as_view(), name="story-like"),
    path("stories/<uuid:uuid>/view/", stories.StoryViewView.as_view(), name="story-view"),
    path(
        "stories/<uuid:uuid>/viewers/",
        social_views.StoryViewerListView.as_view(),
        name="story-viewers",
    ),
    path("comments/<uuid:uuid>/", comments.CommentDetailView.as_view(), name="comment"),
    path("comments/<uuid:uuid>/vote/", comments.CommentVoteView.as_view(), name="comment-vote"),
    path(
        "comments/<uuid:uuid>/replies/",
        comments.CommentReplyListView.as_view(),
        name="comment-replies",
    ),
]
