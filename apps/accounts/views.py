from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect
from django.contrib.auth import logout

from rest_framework import generics, permissions

from .forms import UserRegisterForm, UserProfileForm
from .models import User
from .serializers import RegisterSerializer, UserSerializer
from .forms import UserProfileForm
from .models import EmployeeProfile


# ---------- VUES HTML ----------

class CustomLoginView(LoginView):
    template_name = "user/auth/login.html"


def logout_view(request):
    """
    Déconnexion simple via GET/POST, puis redirection vers la home.
    """
    logout(request)
    return redirect('core:home') 


def register_view(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)   # connecter automatiquement après inscription
            return redirect('core:home')
    else:
        form = UserRegisterForm()
    return render(request, "user/auth/register.html", {"form": form})


@login_required
def profile_view(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, "user/profile.html", {"form": form})


# ---------- API DRF ----------

class RegisterAPI(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileAPI(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
    

@login_required
def profile_view(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
    else:
        form = UserProfileForm(instance=request.user)

    # Récupérer le profil employé s'il existe
    employee_profile = getattr(request.user, "employee_profile", None)

    return render(request, "user/profile.html", {
        "form": form,
        "employee_profile": employee_profile,
    })
