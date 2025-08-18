from django.db.models import Min
from django.shortcuts import redirect
from django.utils.timezone import now

from root.models import FollowRelation
from root.models import NotificationPost
from root.models import SocialUser


class LegalRequirementMixin:
    def dispatch(self, request, *args, **kwargs):

        if not request.user.legaluser.privacy:
            return redirect("privacy")

        if not request.user.legaluser.terms:
            return redirect("terms")

        if not request.user.legaluser.disclaimer:
            return redirect("disclaimer")

        return super().dispatch(request, *args, **kwargs)


class ProtectionRequirementMixin:
    def dispatch(self, request, *args, **kwargs):

        if request.user.legaluser.protection is None:
            return redirect("pedoguard")

        return super().dispatch(request, *args, **kwargs)


class FriendRequestMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            try:
                social_user = SocialUser.objects.get(user=self.request.user)
                context["requests"] = social_user.received_requests.count()
            except SocialUser.DoesNotExist:
                context["requests"] = 0
        return context


class ActivitiesMixin:
    def get_notification_posts(self):
        user = self.request.user

        followed_users = FollowRelation.objects.filter(
            from_user__user=user
        ).values_list("to_user", flat=True)

        follow_dates = (
            FollowRelation.objects.filter(from_user__user=user)
            .values("to_user")
            .annotate(follow_date=Min("created_at"))
        )

        follow_date_dict = {
            entry["to_user"]: entry["follow_date"] for entry in follow_dates
        }

        notification_posts = NotificationPost.objects.filter(
            post__author__id__in=followed_users
        ).exclude(read_by=user)

        return [
            notification
            for notification in notification_posts
            if notification.post.created_at
            >= follow_date_dict.get(notification.post.author.id, now())
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notification_posts = self.get_notification_posts()
        context["notification_posts"] = len(notification_posts)
        return context


class NotificationMixin(FriendRequestMixin, ActivitiesMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(FriendRequestMixin.get_context_data(self, **kwargs))
        context.update(ActivitiesMixin.get_context_data(self, **kwargs))
        return context
