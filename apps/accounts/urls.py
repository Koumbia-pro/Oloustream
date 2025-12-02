from django.urls import path
from django.contrib.auth import views as auth_views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    CustomLoginView,
    logout_view, 
    register_view,
    profile_view,
    RegisterAPI,
    ProfileAPI,
)

app_name = "accounts"

urlpatterns = [
    # ---------- HTML ----------
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('profile/', profile_view, name='profile'),

    # Mot de passe oublié (Django fournit les vues)
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='user/auth/password_reset.html'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='user/auth/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='user/auth/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='user/auth/password_reset_complete.html'
    ), name='password_reset_complete'),

    # ---------- API REST ----------
    path('api/register/', RegisterAPI.as_view(), name='api_register'),
    path('api/profile/', ProfileAPI.as_view(), name='api_profile'),

    # JWT (pour l’API – login / refresh)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]