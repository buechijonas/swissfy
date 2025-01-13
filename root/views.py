from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic import TemplateView

from root.forms import LoginForm, SignUpForm
from root.mixins import LegalRequirementMixin
from root.models import ConfigUser, DetailUser, LegalUser, Role, SocialUser

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
    generic.ListView,
):
    model = User
    template_name = "pages/home.html"


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
