import time

from django.core.management.base import BaseCommand

from posts import videos
from posts.models import Post

POLL_SECONDS = 5


class Command(BaseCommand):
    help = "Transcodes uploaded post videos and creates their thumbnails."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Process pending videos and exit instead of polling.",
        )

    def handle(self, *args, **options):
        while True:
            post = Post.objects.filter(video_status=Post.VideoStatus.PROCESSING).first()
            if post:
                self.process(post)
            elif options["once"]:
                return
            else:
                time.sleep(POLL_SECONDS)

    def process(self, post):
        changes = {"video_upload": ""}
        try:
            video, thumbnail, width, height = videos.transcode(post.video_upload.path)
        except (videos.InvalidVideo, OSError, ValueError) as error:
            self.stderr.write(f"Post {post.pk}: {error}")
            changes["video_status"] = Post.VideoStatus.FAILED
        else:
            post.video.save(video.name, video, save=False)
            post.thumbnail.save(thumbnail.name, thumbnail, save=False)
            changes.update(
                video=post.video.name,
                thumbnail=post.thumbnail.name,
                image_width=width,
                image_height=height,
                video_status=Post.VideoStatus.READY,
            )

        if not Post.objects.filter(pk=post.pk).update(**changes):
            post.video.delete(save=False)
            post.thumbnail.delete(save=False)
        post.video_upload.delete(save=False)
        self.stdout.write(f"Post {post.pk}: {changes['video_status']}")
