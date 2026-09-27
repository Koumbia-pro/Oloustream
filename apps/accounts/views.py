from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from rest_framework import generics, permissions

from apps.core.ratelimit import RateLimiter, client_ip

from .forms import LoginForm, UserProfileForm, UserRegisterForm
from .serializers import RegisterSerializer, UserSerializer

login_limiter = RateLimiter(
    "login",
    limit=getattr(settings, "LOGIN_MAX_ATTEMPTS", 5),
    window_seconds=getattr(settings, "LOGIN_LOCKOUT_SECONDS", 15 * 60),
)
register_limiter = RateLimiter("register", limit=5, window_seconds=60 * 60)


# ---------- VUES HTML ----------

class CustomLoginView(LoginView):
    template_name = "user/auth/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def _identifiers(self):
        username = (self.request.POST.get("username") or "").strip().lower()
        return [f"ip:{client_ip(self.request)}", f"user:{username}"]

    def post(self, request, *args, **kwargs):
        if any(login_limiter.is_blocked(i) for i in self._identifiers()):
            form = self.get_form()
            form.add_error(None, "Trop de tentatives de connexion. Réessayez dans 15 minutes "
                                 "ou réinitialisez votre mot de passe.")
            return self.form_invalid(form)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        if self.request.method == "POST":
            for identifier in self._identifiers():
                login_limiter.hit(identifier)
        return super().form_invalid(form)

    def form_valid(self, form):
        for identifier in self._identifiers():
            login_limiter.reset(identifier)
        if not form.cleaned_data.get("remember_me"):
            self.request.session.set_expiry(0)  # expire à la fermeture du navigateur
        return super().form_valid(form)

    def get_default_redirect_url(self):
        user = self.request.user
        if user.is_staff:
            return "/dashboard/"
        if getattr(user, "business_partner", None) is not None:
            return "/partenaires/dashboard/"
        return super().get_default_redirect_url()


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "Vous êtes déconnecté. À bientôt !")
    return redirect("core:home")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        ip = client_ip(request)
        if register_limiter.is_blocked(ip):
            form.add_error(None, "Trop d'inscriptions depuis cette connexion. Réessayez plus tard.")
        elif form.is_valid():
            register_limiter.hit(ip)
            user = form.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, f"Bienvenue {user.first_name or user.username} ! Votre compte a été créé.")
            return redirect("core:home")
    else:
        form = UserRegisterForm()
    return render(request, "user/auth/register.html", {"form": form})


@login_required
def profile_view(request):
    form = UserProfileForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)

    if request.method == "POST":
        if request.POST.get("action") == "password":
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Votre mot de passe a été modifié.")
                return redirect("accounts:profile")
        else:
            form = UserProfileForm(request.POST, request.FILES, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "Votre profil a été mis à jour.")
                return redirect("accounts:profile")

    return render(request, "user/profile.html", {
        "form": form,
        "password_form": password_form,
        "employee_profile": getattr(request.user, "employee_profile", None),
        "reservations_count": request.user.reservations.count(),
    })


# ---------- API DRF ----------

class RegisterAPI(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileAPI(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
