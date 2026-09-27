from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import CustomLoginView, ProfileAPI, RegisterAPI, logout_view, profile_view, register_view

app_name = "accounts"

urlpatterns = [
    # ---------- HTML ----------
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('profile/', profile_view, name='profile'),
    # Mot de passe oublié : routes globales dans oloustream/urls.py

    # ---------- API REST ----------
    path('api/register/', RegisterAPI.as_view(), name='api_register'),
    path('api/profile/', ProfileAPI.as_view(), name='api_profile'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
