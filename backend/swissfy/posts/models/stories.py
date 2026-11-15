from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Case, Exists, IntegerField, OuterRef, Prefetch, Q, Value, When
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from commons.models import BaseModel, EncryptedTextField, UUIDModel, boolean, count_of
from swissfy.accounts.roles import is_admin
from swissfy.social.models import Member

from .audience import (
    Audience,
    AudienceQuerySet,
    ContactGroup,
    by_suspended_author,
    shared_with_viewer,
)

STORY_TEXT_LENGTH = 200
STORY_LIFETIME = timedelta(hours=24)


def story_cutoff():
    return timezone.now() - STORY_LIFETIME


class StoryQuerySet(AudienceQuerySet):
    def active(self):
        return self.filter(created_at__gte=story_cutoff())

    def apply_acl(self, user, action="read"):
        groups = ContactGroup.objects.filter(stories=OuterRef("pk"))
        stories = self.active().with_audience(user, groups)
        if is_admin(user):
            return stories
        return stories.filter(Q(author=user) | (shared_with_viewer() & ~by_suspended_author()))

    def with_details(self, user):
        own = Q(author=user)
        likes = count_of(StoryLike.objects.all(), "story")
        views = count_of(StoryView.objects.exclude(user=OuterRef("author")), "story")
        return self.annotate(
            is_own=boolean(own),
            liked=Exists(StoryLike.objects.filter(story=OuterRef("pk"), user=user)),
            seen=Exists(StoryView.objects.filter(story=OuterRef("pk"), user=user)),
            like_count=Case(When(own, then=likes), output_field=IntegerField()),
            view_count=Case(When(own, then=views), output_field=IntegerField()),
        )


class Story(UUIDModel):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="stories"
    )
    image = models.FileField(upload_to="stories/")
    text = EncryptedTextField(max_length=STORY_TEXT_LENGTH, blank=True)
    visibility = models.CharField(max_length=20, choices=Audience.choices, default=Audience.PUBLIC)
    groups = models.ManyToManyField(ContactGroup, related_name="stories", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = StoryQuerySet.as_manager()

    def __str__(self):
        return f"Story({self.author}, {self.pk})"

    @property
    def image_url(self):
        return reverse("stories-image", kwargs={"uuid": self.uuid})

    @property
    def expires_at(self):
        return self.created_at + STORY_LIFETIME


class StoryLike(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "story"], name="unique_story_like")]


class StoryView(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="views")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "story"], name="unique_story_view")]


@receiver(post_delete, sender=Story)
def delete_story_image(sender, instance, **kwargs):
    instance.image.delete(save=False)


def authors_for(viewer, lookup="author"):
    authors = Member.objects.select_related("profile").prefetch_related("groups")
    authors = authors.annotate_visibility(viewer)
    if viewer.is_anonymous:
        authors = authors.annotate(has_story=Value(False), has_unseen_story=Value(False))
    else:
        stories = Story.objects.apply_acl(viewer).filter(author=OuterRef("pk"))
        authors = authors.annotate(
            has_story=Exists(stories),
            has_unseen_story=Exists(stories.exclude(views__user=viewer)),
        )
    return Prefetch(lookup, queryset=authors)
