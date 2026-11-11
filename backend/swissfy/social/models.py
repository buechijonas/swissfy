from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following"
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="unique_follow"),
            models.CheckConstraint(condition=~Q(follower=F("following")), name="no_follow_of_self"),
        ]

    def __str__(self):
        return f"{self.follower} follows {self.following}"


class FollowRequest(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_follow_requests"
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_follow_requests",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="unique_follow_request"),
            models.CheckConstraint(
                condition=~Q(follower=F("following")), name="no_follow_request_to_self"
            ),
        ]

    def accept(self):
        Follow.objects.get_or_create(follower=self.follower, following=self.following)
        self.delete()

    def __str__(self):
        return f"{self.follower} -> {self.following}"


class FriendRequest(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_friend_requests"
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_friend_requests",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["sender", "receiver"], name="unique_friend_request"),
            models.CheckConstraint(
                condition=~Q(sender=F("receiver")), name="no_friend_request_to_self"
            ),
        ]

    def accept(self):
        Friendship.objects.get_or_create(user=self.sender, friend=self.receiver)
        Friendship.objects.get_or_create(user=self.receiver, friend=self.sender)
        self.delete()

    def __str__(self):
        return f"{self.sender} -> {self.receiver}"


class Friendship(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="friendships"
    )
    friend = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "friend"], name="unique_friendship"),
            models.CheckConstraint(condition=~Q(user=F("friend")), name="no_friendship_with_self"),
        ]

    def __str__(self):
        return f"{self.user} <-> {self.friend}"


class Block(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocks"
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocked_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "blocked"], name="unique_block"),
            models.CheckConstraint(condition=~Q(user=F("blocked")), name="no_block_of_self"),
        ]

    def __str__(self):
        return f"{self.user} blocks {self.blocked}"


class Nickname(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="given_nicknames"
    )
    target = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    nickname = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["owner", "target"], name="unique_nickname"),
        ]

    def __str__(self):
        return f"{self.owner} -> {self.target}: {self.nickname}"
