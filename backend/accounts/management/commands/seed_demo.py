import base64
import io
import os
import random
from datetime import timedelta
from itertools import product

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw

from accounts.models import AVATAR_CHOICES, UserConsent, UserProfile
from accounts.roles import Role, set_role
from chats.crypto import wrap_message_key
from chats.models import ChatRequest, Message
from moderation.models import Reason, Report, Warning
from moderation.sanctions import WARNING_EXPIRY, suspend
from notifications.models import Notification
from notifications.notify import sync_expired_warnings
from posts import images
from posts.models import (
    Comment,
    CommentVote,
    ContactGroup,
    Like,
    Post,
    PostImage,
    SavedFolder,
    SavedPost,
)
from social.models import Follow, FollowRequest, FriendRequest, Friendship

User = get_user_model()

PREFIX = "demo_"
FIRST_NAMES = ["Anna", "Luca", "Mia", "Noah", "Lea", "Elias", "Lina", "Nico", "Sara", "Jan"]
LAST_NAMES = ["Müller", "Meier", "Schmid", "Keller", "Weber", "Huber", "Steiner", "Brunner"]
TEXTS = [
    "Heute am Zürichsee, was für ein Licht!",
    "Hat jemand Tipps für eine Wanderung im Berner Oberland?",
    "Neues Rezept ausprobiert: Älplermagronen.",
    "Montagmorgen, Kaffee Nummer drei.",
    "Wer kommt am Samstag ans Konzert?",
    "",
]
COMMENTS = ["Wow!", "Sehr schön", "Bin dabei", "Stimmt nicht ganz.", "Danke fürs Teilen", "Haha"]
MESSAGES = ["Hoi, wie gehts?", "Gut und dir?", "Kommst du morgen?", "Ja, bis dann!", "👍"]
IMAGE_SIZES = [(1600, 900), (900, 1600), (1200, 1200)]
NAME_VARIANTS = ["full", "first", "none"]
ROLE_COUNTS = {
    Role.ADMIN: 2,
    Role.MODERATOR: 6,
    Role.SUPPORT: 18,
    Role.VERIFIED: 54,
    Role.DEFAULT: 162,
}
SANCTIONED_EVERY = 4
SANCTIONS = [
    "none",
    "one_warning",
    "two_warnings",
    "expired_warnings",
    "suspended",
    "suspended_with_queue",
    "suspension_ended",
    "suspended_month",
    "suspended_year",
    "lifetime",
]


class Command(BaseCommand):
    help = "Creates demo users with every combination of roles, content, relations and sanctions."

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=42)

    def handle(self, *args, **options):
        self.random = random.Random(options["seed"])
        self.now = timezone.now()
        with transaction.atomic():
            self.reset()
            users = self.create_users()
            self.create_relations(users)
            posts = self.create_posts(users)
            comments = self.create_comments(users, posts)
            self.create_reactions(users, posts, comments)
            self.create_chats(users)
            self.create_reports(users, posts, comments)
            self.create_sanctions(users)
            self.create_notifications(users)
        self.stdout.write(
            self.style.SUCCESS(
                f"{len(users)} Demo-User, {Post.objects.filter(author__in=users).count()} Posts, "
                f"{Comment.objects.filter(author__in=users).count()} Kommentare angelegt."
            )
        )

    def reset(self):
        demo = User.objects.filter(username__startswith=PREFIX)
        Post.objects.filter(author__in=demo).delete()
        demo.delete()

    def past(self, max_days, min_days=0):
        return self.now - timedelta(days=self.random.uniform(min_days, max_days))

    def backdate(self, model, obj, field="created_at", value=None):
        model.objects.filter(pk=obj.pk).update(**{field: value or self.past(60)})

    def create_users(self):
        users = []
        combinations = list(product(NAME_VARIANTS, UserProfile.Visibility))
        roles = [role for role, count in ROLE_COUNTS.items() for _ in range(count)]
        for index, role in enumerate(roles):
            variant, visibility = combinations[index % len(combinations)]
            first = FIRST_NAMES[index % len(FIRST_NAMES)] if variant != "none" else ""
            last = LAST_NAMES[index % len(LAST_NAMES)] if variant == "full" else ""
            user = User.objects.create(
                username=f"{PREFIX}{role.value}_{variant}_{visibility}_{index}",
                first_name=first,
                last_name=last,
            )
            user.set_unusable_password()
            user.save(update_fields=["password"])
            UserProfile.objects.create(
                user=user,
                avatar=AVATAR_CHOICES[index % len(AVATAR_CHOICES)],
                profile_visibility=visibility,
            )
            set_role(user, role)
            UserConsent.objects.create(user=user, privacy=True, terms=True, disclaimer=True)
            sanctioned = role in self.sanctionable and index % SANCTIONED_EVERY == 0
            user.sanction = (
                SANCTIONS[index // SANCTIONED_EVERY % len(SANCTIONS)] if sanctioned else "none"
            )
            users.append(user)
        return users

    @property
    def sanctionable(self):
        return {Role.DEFAULT, Role.VERIFIED, Role.SUPPORT}

    def admins(self):
        return list(User.objects.filter(is_superuser=True))

    def create_relations(self, users):
        everyone = users + self.admins()
        for user in everyone:
            for other in self.random.sample(users, self.random.randint(0, 12)):
                if other == user:
                    continue
                if other.profile.profile_visibility != UserProfile.Visibility.PUBLIC and (
                    self.random.random() < 0.3
                ):
                    FollowRequest.objects.get_or_create(follower=user, following=other)
                else:
                    Follow.objects.get_or_create(follower=user, following=other)

        for user in everyone:
            for other in self.random.sample(users, self.random.randint(0, 4)):
                if other != user:
                    Follow.objects.get_or_create(follower=user, following=other)
                    Follow.objects.get_or_create(follower=other, following=user)

        follows = set(
            Follow.objects.filter(follower__in=everyone).values_list("follower", "following")
        )
        mutual = {tuple(sorted(pair)) for pair in follows if pair[::-1] in follows}
        for a, b in sorted(mutual):
            if self.random.random() < 0.7:
                Friendship.objects.get_or_create(user_id=a, friend_id=b)
                Friendship.objects.get_or_create(user_id=b, friend_id=a)
            elif self.random.random() < 0.4:
                FriendRequest.objects.get_or_create(sender_id=a, receiver_id=b)

    def image_upload(self, size, index):
        image = Image.new("RGB", size, self.random.choice(["#c0392b", "#2980b9", "#27ae60"]))
        draw = ImageDraw.Draw(image)
        draw.ellipse([size[0] // 4, size[1] // 4, size[0] * 3 // 4, size[1] * 3 // 4], "#ffffff")
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        return SimpleUploadedFile(f"demo-{index}.jpg", buffer.getvalue(), "image/jpeg")

    def create_posts(self, users):
        posts = []
        for index, user in enumerate(users):
            group = ContactGroup.objects.create(owner=user, name="Familie")
            group.members.set(self.random.sample(users, 3))
            for number in range(index % 5):
                visibility = list(Post.Visibility)[(index + number) % len(Post.Visibility)]
                text = TEXTS[(index + number) % len(TEXTS)]
                post = Post(author=user, text=text or "Ohne Worte", visibility=visibility)
                image_count = (index + number) % 4
                if image_count:
                    uploads = [
                        self.image_upload(IMAGE_SIZES[(number + i) % 3], i)
                        for i in range(image_count)
                    ]
                    files, post.thumbnail, post.image_width, post.image_height = images.compress(
                        uploads
                    )
                    if not text:
                        post.text = ""
                post.save()
                if visibility == Post.Visibility.GROUPS:
                    post.groups.add(group)
                if image_count:
                    PostImage.objects.bulk_create(
                        PostImage(post=post, file=file, position=position)
                        for position, file in enumerate(files)
                    )
                self.backdate(Post, post)
                posts.append(post)
        return posts

    def create_comments(self, users, posts):
        comments = []
        everyone = users + self.admins()
        for post in posts:
            level = [None]
            for depth in range(3):
                next_level = []
                for parent in level:
                    for _ in range(self.random.randint(0, 3 - depth)):
                        comment = Comment.objects.create(
                            post=post,
                            parent=parent,
                            author=self.random.choice(everyone),
                            text=self.random.choice(COMMENTS),
                        )
                        self.backdate(Comment, comment, value=self.past(30))
                        next_level.append(comment)
                comments.extend(next_level)
                level = next_level
        return comments

    def create_reactions(self, users, posts, comments):
        everyone = users + self.admins()
        for user in everyone:
            folder, _ = SavedFolder.objects.get_or_create(owner=user, name="Lieblinge")
            for post in self.random.sample(posts, min(len(posts), 8)):
                Like.objects.get_or_create(user=user, post=post)
                if self.random.random() < 0.3:
                    SavedPost.objects.get_or_create(
                        user=user,
                        post=post,
                        defaults={"folder": folder if self.random.random() < 0.5 else None},
                    )
            for comment in self.random.sample(comments, min(len(comments), 15)):
                if comment.author_id != user.pk:
                    CommentVote.objects.get_or_create(
                        user=user, comment=comment, defaults={"value": self.random.choice([1, -1])}
                    )

    def create_message(self, sender, recipient, text, created_at):
        message_key = AESGCM.generate_key(bit_length=256)
        iv = os.urandom(12)
        ciphertext = AESGCM(message_key).encrypt(iv, text.encode(), None)
        message = Message(
            sender=sender,
            recipient=recipient,
            ciphertext=base64.b64encode(ciphertext).decode(),
            iv=base64.b64encode(iv).decode(),
        )
        message.server_key = wrap_message_key(message, message_key)
        message.save()
        state = self.random.choice(["sent", "delivered", "read", "seen"])
        fields = {"created_at": created_at}
        if state != "sent":
            fields["delivered_at"] = created_at
        if state in ("read", "seen"):
            fields["read_at"] = created_at
        if state == "seen":
            fields["seen_at"] = created_at
        Message.objects.filter(pk=message.pk).update(**fields)

    def create_chats(self, users):
        everyone = users + self.admins()
        statuses = list(ChatRequest.Status)
        for index, sender in enumerate(everyone):
            for recipient in self.random.sample(users, 3):
                if recipient == sender or ChatRequest.between(sender, recipient):
                    continue
                status = statuses[(index + recipient.pk) % len(statuses)]
                ChatRequest.objects.create(sender=sender, recipient=recipient, status=status)
                if status != ChatRequest.Status.ACCEPTED:
                    continue
                start = self.now - timedelta(days=self.random.uniform(1, 10))
                for number in range(self.random.randint(1, 8)):
                    author, partner = (
                        (sender, recipient) if number % 2 == 0 else (recipient, sender)
                    )
                    self.create_message(
                        author,
                        partner,
                        MESSAGES[number % len(MESSAGES)],
                        start + timedelta(minutes=7 * number),
                    )

    def create_reports(self, users, posts, comments):
        for target in self.random.sample(posts, min(len(posts), 10)) + self.random.sample(
            comments, min(len(comments), 10)
        ):
            field = "post" if isinstance(target, Post) else "comment"
            reporters = [user for user in users if user.pk != target.author_id]
            for reporter in self.random.sample(reporters, self.random.randint(1, 4)):
                Report.objects.get_or_create(reporter=reporter, **{field: target})

    def warned_content(self, user, created_at):
        if self.random.random() < 0.5:
            post = Post.objects.create(
                author=user, text="Unangebrachter Inhalt", hidden_at=self.now
            )
            Post.objects.filter(pk=post.pk).update(created_at=created_at)
            return {"post": post}
        post = self.random.choice(list(Post.objects.filter(author__username__startswith=PREFIX)))
        comment = Comment.objects.create(
            post=post, author=user, text="Unangebrachter Kommentar", hidden_at=self.now
        )
        Comment.objects.filter(pk=comment.pk).update(created_at=created_at)
        return {"comment": comment}

    def warn(self, user, days_ago):
        created_at = self.now - timedelta(days=days_ago)
        target = self.warned_content(user, created_at)
        moderator = User.objects.filter(username__startswith=f"{PREFIX}moderator").first()
        Report.objects.create(reporter=moderator, resolved_at=self.now, **target)
        warning = Warning.objects.create(
            user=user, moderator=moderator, reason=self.random.choice(Reason.values), **target
        )
        Warning.objects.filter(pk=warning.pk).update(created_at=created_at)
        return warning

    def warnings_then_suspension(self, user, step, starts_days_ago):
        warnings = [self.warn(user, starts_days_ago + offset) for offset in (2, 1, 0)]
        for _ in range(step):
            warnings.append(self.warn(user, starts_days_ago))
        start = self.now - timedelta(days=starts_days_ago)
        return suspend(user, warnings[-1], step, start)

    def create_sanctions(self, users):
        expired = WARNING_EXPIRY.days + 10
        for user in users:
            match user.sanction:
                case "one_warning":
                    self.warn(user, 5)
                case "two_warnings":
                    self.warn(user, 20)
                    self.warn(user, 2)
                case "expired_warnings":
                    self.warn(user, expired + 30)
                    self.warn(user, expired)
                    self.warn(user, 10)
                case "suspended":
                    self.warnings_then_suspension(user, 0, 1)
                case "suspended_with_queue":
                    first = self.warnings_then_suspension(user, 0, 1)
                    queued = self.warn(user, 0)
                    suspend(user, queued, 1, first.ends_at)
                case "suspension_ended":
                    self.warnings_then_suspension(user, 0, 40)
                case "suspended_month":
                    self.warnings_then_suspension(user, 2, 3)
                case "suspended_year":
                    self.warnings_then_suspension(user, 3, 10)
                case "lifetime":
                    self.warnings_then_suspension(user, 4, 5)

    def create_notifications(self, users):
        Kind = Notification.Kind
        everyone = users + self.admins()
        read_before = self.now - timedelta(days=2)
        notifications = []

        def add(recipient_id, kind, created_at, actor_id=None, **targets):
            if recipient_id == actor_id:
                return
            notifications.append(
                Notification(
                    recipient_id=recipient_id,
                    kind=kind,
                    actor_id=actor_id,
                    created_at=created_at,
                    read_at=created_at if created_at < read_before else None,
                    **targets,
                )
            )

        for comment in Comment.objects.filter(post__author__in=everyone).select_related("post"):
            add(
                comment.post.author_id,
                Kind.COMMENT,
                comment.created_at,
                comment.author_id,
                post_id=comment.post_id,
                comment=comment,
            )
        for like in Like.objects.filter(post__author__in=everyone).select_related("post"):
            add(like.post.author_id, Kind.LIKE, self.past(10), like.user_id, post_id=like.post_id)
        for follow in Follow.objects.filter(following__in=everyone):
            add(follow.following_id, Kind.FOLLOW, self.past(30), follow.follower_id)
        for request in FollowRequest.objects.filter(following__in=everyone):
            add(request.following_id, Kind.FOLLOW_REQUEST, self.past(5), request.follower_id)
        for request in FriendRequest.objects.filter(receiver__in=everyone):
            add(request.receiver_id, Kind.FRIEND_REQUEST, self.past(5), request.sender_id)
        for warning in Warning.objects.filter(user__in=users):
            add(warning.user_id, Kind.WARNING, warning.created_at, warning=warning)
        Notification.objects.bulk_create(notifications, batch_size=2000)
        for notification in Notification.objects.filter(
            kind=Kind.SUSPENSION, recipient__in=users, suspension__warning__isnull=False
        ).select_related("suspension__warning"):
            issued_at = notification.suspension.warning.created_at + timedelta(seconds=1)
            Notification.objects.filter(pk=notification.pk).update(
                created_at=issued_at, read_at=issued_at if issued_at < read_before else None
            )
        for user in users:
            sync_expired_warnings(user)
