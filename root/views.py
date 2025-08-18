from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Min
from django.db.models import OuterRef
from django.db.models import Q
from django.db.models import Subquery
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.utils.translation import gettext as _
from django.views import generic
from django.views import View
from django.views.generic import TemplateView

from root.forms import LoginForm
from root.forms import SignUpForm
from root.mixins import LegalRequirementMixin
from root.mixins import NotificationMixin
from root.mixins import ProtectionRequirementMixin
from root.models import Commentary
from root.models import ConfigUser
from root.models import DetailUser
from root.models import FollowRelation
from root.models import LegalUser
from root.models import LinkedUser
from root.models import Nickname
from root.models import NotificationPost
from root.models import Post
from root.models import Role
from root.models import SocialUser


User = get_user_model()


# Create your views here.
def sign_in(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect("home")
        form = LoginForm()
        return render(request, "pages/login.html", {"form": form})

    elif request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, "Erfolgreich angemeldet!")
                return redirect("home")

        messages.error(request, "Benutzername oder Passwort ist falsch.")
        return render(request, "pages/login.html", {"form": form})


class SignUpView(generic.CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy("login")
    template_name = "pages/signup.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        LegalUser.objects.create(
            user=self.object, privacy=False, disclaimer=False, terms=False
        )
        default_role = Role.objects.get(name="Standard")
        ConfigUser.objects.create(
            user=self.object,
            role=default_role,
        )
        SocialUser.objects.create(
            user=self.object,
        )
        DetailUser.objects.create(
            user=self.object,
        )
        LinkedUser.objects.create(
            user=self.object,
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


@login_required
def custom_logout(request):
    logout(request)
    return redirect("home")


class HomeView(
    LoginRequiredMixin,
    LegalRequirementMixin,
    ProtectionRequirementMixin,
    NotificationMixin,
    generic.ListView,
):
    model = Post
    template_name = "pages/home.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        social_user = SocialUser.objects.get(user=self.request.user)
        followed_users = social_user.follow.all()

        return Post.objects.filter(author__in=followed_users).order_by("-created_at")


def load_more_posts(request):
    if request.method == "GET" and request.user.is_authenticated:
        offset = int(request.GET.get("offset", 0))
        limit = 10

        social_user = SocialUser.objects.get(user=request.user)
        followed_users = social_user.follow.all()

        posts = Post.objects.filter(author__in=followed_users).order_by("-created_at")[
            offset : offset + limit
        ]

        posts_data = []
        for post in posts:
            post_data = {
                "id": post.id,
                "text": post.text,
                "image": post.image.url if post.image else None,
                "author": {
                    "pk": post.author.pk,
                    "username": post.author.username,
                    "first_name": post.author.first_name,
                    "last_name": post.author.last_name,
                    "role": (
                        post.author.config.role.name
                        if hasattr(post.author, "config")
                        else None
                    ),
                    "profile_image": (
                        post.author.detailuser.image.url
                        if hasattr(post.author, "detailuser")
                        and post.author.detailuser.image
                        else None
                    ),
                },
                "likes_count": post.likes.count(),
                "liked": request.user in post.likes.all(),
                "created_at": post.created_at.strftime("%d.%m.%Y %H:%M"),
            }
            posts_data.append(post_data)

        return JsonResponse({"posts": posts_data})

    return JsonResponse({"error": "Ungültige Anfrage"}, status=400)


@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user

    if user in post.likes.all():
        post.likes.remove(user)
        liked = False
    else:
        post.likes.add(user)
        liked = True

    return JsonResponse({"liked": liked, "likes_count": post.likes.count()})


class MaintenanceView(TemplateView):
    model = User
    template_name = "pages/maintenance.html"


class SearchView(
    LoginRequiredMixin,
    LegalRequirementMixin,
    ProtectionRequirementMixin,
    NotificationMixin,
    generic.ListView,
):
    model = User
    template_name = "pages/search.html"
    context_object_name = "users"

    def get_queryset(self):
        query = self.request.GET.get("query", "")
        qs = User.objects.select_related("config__role").exclude(
            pk=self.request.user.pk
        )

        if query:
            qs = qs.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(username__icontains=query)
            )

        return qs.order_by(
            "-config__role__priority", "first_name", "last_name", "username"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Benutzerliste")
        return context


class CreatePostView(
    LoginRequiredMixin,
    LegalRequirementMixin,
    ProtectionRequirementMixin,
    NotificationMixin,
    generic.CreateView,
):
    model = Post
    fields = ["image", "text"]
    template_name = "pages/post_update.html"

    def get_success_url(self):
        return reverse("profile", kwargs={"pk": self.request.user.pk}) + "?tab=2"

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        NotificationPost.objects.create(post=self.object)

        return response

    def form_invalid(self, form):
        return super().form_invalid(form)


class DetailPostView(
    LoginRequiredMixin,
    LegalRequirementMixin,
    ProtectionRequirementMixin,
    NotificationMixin,
    generic.DetailView,
):
    model = Post
    template_name = "pages/post.html"


@login_required
def commentary_create(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        if text:
            Commentary.objects.create(post=post, author=request.user, text=text)
    return redirect("post", pk=post.pk)


class UpdatePostView(
    LoginRequiredMixin,
    LegalRequirementMixin,
    ProtectionRequirementMixin,
    NotificationMixin,
    generic.UpdateView,
):
    model = Post
    fields = ["image", "text"]
    template_name = "pages/post_update.html"

    def get_success_url(self):
        return reverse("profile", kwargs={"pk": self.request.user.pk}) + "?tab=2"

    def form_valid(self, form):
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)


class DeletePostView(
    LoginRequiredMixin,
    LegalRequirementMixin,
    ProtectionRequirementMixin,
    NotificationMixin,
    generic.DeleteView,
):
    model = Post
    template_name = "pages/post_delete.html"

    def get_success_url(self):
        return reverse("profile", kwargs={"pk": self.request.user.pk}) + "?tab=2"


class UpdateCommentaryView(
    LoginRequiredMixin,
    LegalRequirementMixin,
    ProtectionRequirementMixin,
    NotificationMixin,
    generic.UpdateView,
):
    model = Commentary
    fields = ["text"]
    template_name = "pages/commentary_update.html"

    def form_valid(self, form):
        return super().form_valid(form)

    def form_imvalid(self, form):
        return super().form_invalid(form)


class NotificationView(
    LoginRequiredMixin,
    LegalRequirementMixin,
    ProtectionRequirementMixin,
    NotificationMixin,
    TemplateView,
):
    model = User
    template_name = "pages/notification.html"


class NotificationFriendRequestView(
    LoginRequiredMixin,
    LegalRequirementMixin,
    ProtectionRequirementMixin,
    NotificationMixin,
    generic.ListView,
):
    model = User
    template_name = "pages/notification_friend_request.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        social_user = SocialUser.objects.get(user=self.request.user)
        context["notifications"] = social_user.received_requests.all()
        return context


class NotificationAcitivitesView(
    LoginRequiredMixin,
    LegalRequirementMixin,
    ProtectionRequirementMixin,
    NotificationMixin,
    generic.ListView,
):
    model = NotificationPost
    template_name = "pages/notification_activities.html"

    def get_queryset(self):
        user = self.request.user

        # Alle User, denen der aktuelle Nutzer folgt
        followed_users = FollowRelation.objects.filter(
            from_user__user=user
        ).values_list("to_user", flat=True)

        # Das Follow-Datum für jeden gefolgten User abrufen
        follow_dates = (
            FollowRelation.objects.filter(from_user__user=user)
            .values("to_user")
            .annotate(follow_date=Min("created_at"))
        )

        # Dictionary mit {user_id: follow_date}
        follow_date_dict = {
            entry["to_user"]: entry["follow_date"] for entry in follow_dates
        }

        filtered_notifications = NotificationPost.objects.filter(
            post__author__id__in=followed_users
        ).exclude(
            read_by=user  # Ausschließen, wenn der User die Benachrichtigung schon gelesen hat
        )

        filtered_notifications = [
            notification
            for notification in filtered_notifications
            if notification.post.created_at
            >= follow_date_dict.get(notification.post.author.id, now())
        ]

        self.filtered_notifications = filtered_notifications

        return filtered_notifications

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filtered_notifications"] = self.filtered_notifications
        return context


class ProfileView(
    LoginRequiredMixin,
    LegalRequirementMixin,
    ProtectionRequirementMixin,
    NotificationMixin,
    generic.DetailView,
):
    model = User
    template_name = "pages/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_user_social, created = SocialUser.objects.get_or_create(
            user=self.request.user
        )
        user = self.object
        social_user = SocialUser.objects.get(user=user)
        request_user_social = SocialUser.objects.get(user=self.request.user)

        is_friend = user in current_user_social.friends.all()
        is_friend_request_sent = user in current_user_social.sent_requests.all()
        is_friend_request_received = user in current_user_social.received_requests.all()
        is_blocked = user in current_user_social.blocked.all()

        context["followers"] = social_user.follow.count()
        context["following"] = SocialUser.objects.filter(follow=user).count()
        tab = self.request.GET.get("tab", "1")
        context["tab"] = int(tab)
        context["is_following"] = social_user.user in request_user_social.follow.all()
        context["is_friend"] = is_friend
        context["is_friend_request_sent"] = is_friend_request_sent
        context["is_friend_request_received"] = is_friend_request_received
        context["is_blocked"] = is_blocked

        detail_infos = {
            "sex": bool(user.detailuser.sex),
            "birthday": bool(user.detailuser.birthday),
            "profession": bool(user.detailuser.profession),
            "place_of_residence": bool(user.detailuser.place_of_residence),
            "place_of_origin": bool(user.detailuser.place_of_origin),
            "relationship": bool(user.detailuser.relationship),
        }

        linked_accounts = {
            "discord": bool(user.linkeduser.discord),
            "epicgames": bool(user.linkeduser.epicgames),
            "facebook": bool(user.linkeduser.facebook),
            "instagram": bool(user.linkeduser.instagram),
            "linkedin": bool(user.linkeduser.linkedin),
            "pinterest": bool(user.linkeduser.pinterest),
            "playstation": bool(user.linkeduser.playstation),
            "reddit": bool(user.linkeduser.reddit),
            "snapchat": bool(user.linkeduser.snapchat),
            "steam": bool(user.linkeduser.steam),
            "threads": bool(user.linkeduser.threads),
            "tiktok": bool(user.linkeduser.tiktok),
            "twitter": bool(user.linkeduser.twitter),
            "xbox": bool(user.linkeduser.xbox),
            "youtube": bool(user.linkeduser.youtube),
        }

        context["has_detail_infos"] = any(detail_infos.values())
        context["has_linked_accounts"] = any(linked_accounts.values())

        return context


class ProfileFriendsView(
    LoginRequiredMixin,
    LegalRequirementMixin,
    ProtectionRequirementMixin,
    NotificationMixin,
    generic.DetailView,
):
    model = User
    template_name = "pages/search.html"
    context_object_name = "user"

    def get_queryset(self):
        return User.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()  # Der angezeigte Benutzer (Detailansicht)
        context["title"] = _("Freunde von {first_name} {last_name}").format(
            first_name=user.first_name,
            last_name=user.last_name,
        )
        context["users"] = user.socialuser.friends.all()

        return context


class ProfileFollowersView(
    LoginRequiredMixin,
    LegalRequirementMixin,
    ProtectionRequirementMixin,
    NotificationMixin,
    generic.DetailView,
):
    model = User
    template_name = "pages/search.html"
    context_object_name = "user"

    def get_queryset(self):
        return User.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()

        context["title"] = _("Follower von {first_name} {last_name}").format(
            first_name=user.first_name,
            last_name=user.last_name,
        )

        social_user = SocialUser.objects.get(user=user)

        context["users"] = User.objects.filter(socialuser__follow=social_user.user)

        return context


class ProfileFollowingView(
    LoginRequiredMixin,
    LegalRequirementMixin,
    ProtectionRequirementMixin,
    NotificationMixin,
    generic.DetailView,
):
    model = User
    template_name = "pages/search.html"
    context_object_name = "user"

    def get_queryset(self):
        return User.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context["title"] = _("{first_name} {last_name} folgt").format(
            first_name=user.first_name,
            last_name=user.last_name,
        )
        context["users"] = user.socialuser.follow.all()

        return context


@login_required
def follow_user(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    social_user, created = SocialUser.objects.get_or_create(user=request.user)
    target_social_user, created = SocialUser.objects.get_or_create(user=target_user)

    # Toggle follow/unfollow
    if target_user in social_user.follow.all():
        social_user.follow.remove(target_user)
        messages.success(request, f"Du folgst {target_user.username} nicht mehr.")
    else:
        social_user.follow.add(target_user)
        messages.success(request, f"Du folgst {target_user.username} jetzt.")

    # Cancel friend request if exists
    if target_user in social_user.sent_requests.all():
        social_user.sent_requests.remove(target_user)
        target_social_user.received_requests.remove(request.user)
        messages.info(
            request, f"Freundschaftsanfrage an {target_user.username} wurde storniert."
        )

    # Unfriend if they are friends
    if target_user in social_user.friends.all():
        social_user.friends.remove(target_user)
        target_social_user.friends.remove(request.user)
        messages.info(
            request, f"Du bist nicht mehr mit {target_user.username} befreundet."
        )

    return redirect(reverse("profile", kwargs={"pk": user_id}))


class SendFriendRequestView(LoginRequiredMixin, View):
    def post(self, request, pk):
        user_to_request = get_object_or_404(User, pk=pk)
        if user_to_request != request.user:
            current_user_social, created = SocialUser.objects.get_or_create(
                user=request.user
            )
            user_to_request_social, created = SocialUser.objects.get_or_create(
                user=user_to_request
            )
            if user_to_request not in current_user_social.sent_requests.all():
                current_user_social.sent_requests.add(user_to_request)
                user_to_request_social.received_requests.add(request.user)
        return redirect(reverse("profile", kwargs={"pk": pk}))


class AcceptFriendRequestView(LoginRequiredMixin, View):
    def post(self, request, pk):
        user_to_accept = get_object_or_404(User, pk=pk)
        social_user = SocialUser.objects.get(user=request.user)
        user_to_accept_social = SocialUser.objects.get(user=user_to_accept)

        if user_to_accept in social_user.received_requests.all():
            social_user.friends.add(user_to_accept)
            if user_to_accept not in social_user.follow.all():
                social_user.follow.add(user_to_accept)
            social_user.received_requests.remove(user_to_accept)
            user_to_accept_social.friends.add(request.user)
            if request.user not in user_to_accept_social.follow.all():
                user_to_accept_social.follow.add(request.user)
            user_to_accept_social.sent_requests.remove(request.user)

        return redirect(reverse("notification_friend_request"))


class DeclineFriendRequestView(LoginRequiredMixin, View):
    def post(self, request, pk):
        user_to_decline = get_object_or_404(User, pk=pk)
        social_user = SocialUser.objects.get(user=request.user)

        if user_to_decline in social_user.received_requests.all():
            social_user.received_requests.remove(user_to_decline)
            user_to_decline_social = SocialUser.objects.get(user=user_to_decline)
            user_to_decline_social.sent_requests.remove(request.user)

        return redirect(reverse("notification"))


class CancelFriendRequestView(LoginRequiredMixin, View):
    def post(self, request, pk):
        user_to_cancel = get_object_or_404(User, pk=pk)
        if user_to_cancel != request.user:
            current_user_social, created = SocialUser.objects.get_or_create(
                user=request.user
            )
            user_to_cancel_social, created = SocialUser.objects.get_or_create(
                user=user_to_cancel
            )
            if user_to_cancel in current_user_social.sent_requests.all():
                current_user_social.sent_requests.remove(user_to_cancel)
                user_to_cancel_social.received_requests.remove(request.user)
        return redirect(reverse("profile", kwargs={"pk": pk}))


class RemoveFriendView(LoginRequiredMixin, View):
    def post(self, request, pk):
        user_to_remove = get_object_or_404(User, pk=pk)
        if user_to_remove != request.user:
            current_user_social, created = SocialUser.objects.get_or_create(
                user=request.user
            )
            user_to_remove_social, created = SocialUser.objects.get_or_create(
                user=user_to_remove
            )

            if user_to_remove in current_user_social.friends.all():
                current_user_social.friends.remove(user_to_remove)
                user_to_remove_social.friends.remove(request.user)

        return redirect(reverse("profile", kwargs={"pk": pk}))


class AccountView(
    LoginRequiredMixin,
    LegalRequirementMixin,
    ProtectionRequirementMixin,
    NotificationMixin,
    generic.ListView,
):
    model = User
    template_name = "pages/account.html"


class UpdateAccountView(
    LoginRequiredMixin,
    LegalRequirementMixin,
    ProtectionRequirementMixin,
    NotificationMixin,
    generic.UpdateView,
):
    model = DetailUser
    fields = [
        "image",
        "biography",
        "sex",
        "birthday",
        "profession",
        "place_of_residence",
        "place_of_origin",
        "relationship",
    ]
    template_name = "pages/account_update.html"
    success_url = reverse_lazy("account")

    def dispatch(self, request, *args, **kwargs):
        if kwargs.get("pk") != str(request.user.pk):
            correct_url = reverse(
                "account_update", kwargs={"pk": request.user.detailuser.pk}
            )
            if request.path != correct_url:
                return redirect(correct_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        detail_user = form.instance
        legal_user = detail_user.user.legaluser

        if (
            legal_user.protection is False
            and detail_user.birthday
            and (now().date() - detail_user.birthday).days < 18 * 365
        ):
            legal_user.protection = True
            legal_user.save()

            return redirect(reverse("force_pedoguard"))

        return super().form_valid(form)


class UpdateAccountLinksView(
    LoginRequiredMixin,
    LegalRequirementMixin,
    ProtectionRequirementMixin,
    NotificationMixin,
    generic.UpdateView,
):
    model = LinkedUser
    fields = [
        "discord",
        "epicgames",
        "facebook",
        "instagram",
        "linkedin",
        "pinterest",
        "playstation",
        "reddit",
        "snapchat",
        "steam",
        "threads",
        "tiktok",
        "twitter",
        "xbox",
        "youtube",
    ]
    template_name = "pages/account_link_update.html"
    success_url = reverse_lazy("account")

    def dispatch(self, request, *args, **kwargs):
        if kwargs.get("pk") != str(request.user.pk):
            correct_url = reverse(
                "account_link_update", kwargs={"pk": request.user.linkeduser.pk}
            )
            if request.path != correct_url:
                return redirect(correct_url)
        return super().dispatch(request, *args, **kwargs)


class SettingsView(
    LoginRequiredMixin,
    LegalRequirementMixin,
    ProtectionRequirementMixin,
    NotificationMixin,
    generic.ListView,
):
    model = User
    template_name = "pages/settings.html"


class UpdateSettingsView(
    LoginRequiredMixin,
    LegalRequirementMixin,
    ProtectionRequirementMixin,
    NotificationMixin,
    generic.UpdateView,
):
    model = User
    fields = ["first_name", "last_name", "username", "email"]
    template_name = "pages/settings_update.html"
    success_url = reverse_lazy("settings")

    def dispatch(self, request, *args, **kwargs):
        if kwargs.get("pk") != str(request.user.pk):
            correct_url = reverse("settings_update", kwargs={"pk": request.user.pk})
            if request.path != correct_url:
                return redirect(correct_url)
        return super().dispatch(request, *args, **kwargs)


class UpdatePasswordSettingsView(
    LoginRequiredMixin,
    LegalRequirementMixin,
    ProtectionRequirementMixin,
    NotificationMixin,
    generic.UpdateView,
):
    model = User
    fields = ["password"]
    template_name = "pages/settings_pw_update.html"
    success_url = reverse_lazy("settings")

    def dispatch(self, request, *args, **kwargs):
        if kwargs.get("pk") != str(request.user.pk):
            correct_url = reverse("settings_pw_update", kwargs={"pk": request.user.pk})
            if request.path != correct_url:
                return redirect(correct_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.password = make_password(form.cleaned_data["password"])
        return super().form_valid(form)


class ImpressumView(TemplateView):
    model = User
    template_name = "pages/impressum.html"


class PrivacyView(generic.UpdateView):
    model = LegalUser
    fields = []
    template_name = "pages/privacy.html"
    success_url = reverse_lazy("terms")

    def get_object(self, queryset=None):
        if self.request.user.is_authenticated:
            return self.request.user.legaluser

    def form_valid(self, form):
        form.instance.privacy = True
        form.instance.save()

        if not form.instance.terms:
            return redirect("terms")
        elif not form.instance.disclaimer:
            return redirect("disclaimer")
        else:
            return redirect("home")


class TermsView(generic.UpdateView):
    model = LegalUser
    fields = []
    template_name = "pages/terms.html"
    success_url = reverse_lazy("disclaimer")

    def get_object(self, queryset=None):
        if self.request.user.is_authenticated:
            return self.request.user.legaluser

    def form_valid(self, form):
        form.instance.terms = True
        form.instance.save()
        if not form.instance.disclaimer:
            return redirect("disclaimer")
        elif not form.instance.privacy:
            return redirect("privacy")
        else:
            return redirect("home")


class DisclaimerView(generic.UpdateView):
    model = LegalUser
    fields = []
    template_name = "pages/disclaimer.html"
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        if self.request.user.is_authenticated:
            return self.request.user.legaluser

    def form_valid(self, form):
        form.instance.disclaimer = True
        form.instance.save()
        return redirect("home")


class PedoGuardView(generic.UpdateView):
    model = LegalUser
    fields = []
    template_name = "pages/pedoguard.html"
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        if self.request.user.is_authenticated:
            return self.request.user.legaluser

    def post(self, request, *args, **kwargs):
        legal_user = self.get_object()
        if "activate_protection" in request.POST:
            legal_user.protection = True
        elif "deactivate_protection" in request.POST:
            legal_user.protection = False
        legal_user.save()
        return HttpResponseRedirect(self.success_url)


class ForcePedoGuardView(
    LoginRequiredMixin, LegalRequirementMixin, ProtectionRequirementMixin, TemplateView
):
    model = LegalUser
    fields = []
    template_name = "pages/pedoguard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["minor"] = True

        return context


class NicknameCreateView(
    LoginRequiredMixin,
    LegalRequirementMixin,
    ProtectionRequirementMixin,
    generic.CreateView,
):
    models = Nickname
    template_name = "pages/account_nickname_update.html"
