from django.urls import path

from . import files, views

app_name = "core"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("contact/", views.contact_view, name="contact"),
    path("a-propos/", views.AboutView.as_view(), name="about"),
    path("realisations/", views.RealisationsView.as_view(), name="realisations"),
    path("mentions-legales/", views.LegalView.as_view(), name="legal"),
    path("confidentialite/", views.PrivacyView.as_view(), name="privacy"),
    path("fichiers/<slug:kind>/<int:pk>/", files.protected_file, name="protected_file"),
]
