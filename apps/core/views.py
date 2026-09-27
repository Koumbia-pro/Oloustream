
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView

from apps.services_app.models import Partner, Service, Training
from apps.studio.models import Studio

from .forms import ContactRequestForm
from .ratelimit import RateLimiter, client_ip
from .utils import send_safely


contact_limiter = RateLimiter("contact", limit=5, window_seconds=60 * 60)

# Chiffres clés affichés sur le site vitrine
KEY_FIGURES = {
    "projects_count": 936,
    "streaming_views": 29,
    "countries_count": 7,
}


def home_view(request):
    services = Service.objects.filter(is_active=True).select_related("category").order_by("name")[:6]
    partners = Partner.objects.filter(active=True).order_by("name")[:12]
    studios = Studio.objects.filter(is_active=True)[:3]
    trainings = Training.objects.filter(is_active=True).order_by("start_date")[:3]

    context = {
        "services": services,
        "partners": partners,
        "studios": studios,
        "trainings": trainings,
        "hero_video_url": settings.MEDIA_URL + "hero/hero.mp4",
        "partners_count": Partner.objects.filter(active=True).count(),
        "contact_form": ContactRequestForm(),
        **KEY_FIGURES,
    }
    return render(request, "front/home.html", context)


def contact_view(request):
    initial = {}
    if request.GET.get("sujet"):
        initial["subject"] = request.GET["sujet"].upper()
    if request.user.is_authenticated:
        initial.update({
            "full_name": request.user.get_full_name(),
            "email": request.user.email,
            "phone": getattr(request.user, "phone", ""),
        })

    if request.method == "POST":
        ip = client_ip(request)
        form = ContactRequestForm(request.POST)
        if contact_limiter.is_blocked(ip):
            messages.error(request, "Trop de demandes envoyées. Merci de réessayer dans une heure ou de nous appeler.")
        elif form.is_valid():
            contact_limiter.hit(ip)
            contact = form.save(commit=False)
            contact.ip_address = ip or None
            contact.save()
            _notify_team_of_contact(contact)
            messages.success(
                request,
                "Merci ! Votre demande a bien été envoyée. Notre équipe vous répond sous 24 h ouvrées.",
            )
            return redirect("core:contact")
    else:
        form = ContactRequestForm(initial=initial)

    return render(request, "front/contact.html", {"form": form})


def _notify_team_of_contact(contact):
    from apps.accounts.models import User
    from apps.notifications.models import NotificationTypeChoices
    from apps.notifications.services import create_notification

    for admin in User.objects.filter(is_staff=True, is_active=True):
        create_notification(
            user=admin,
            title=f"Nouvelle demande : {contact.get_subject_display()}",
            message=f"{contact.full_name} ({contact.email}) — {contact.message[:150]}",
            notification_type=NotificationTypeChoices.GENERAL,
            target_object=contact,
            link=f"/admin/core/contactrequest/{contact.pk}/change/",
        )

    body = (
        f"Nouvelle demande reçue sur le site.\n\n"
        f"Objet : {contact.get_subject_display()}\n"
        f"Nom : {contact.full_name}\n"
        f"Structure : {contact.company or '-'}\n"
        f"Email : {contact.email}\n"
        f"Téléphone : {contact.phone or '-'}\n"
        f"Date souhaitée : {contact.event_date or '-'}\n"
        f"Budget : {contact.budget or '-'}\n\n"
        f"{contact.message}\n"
    )
    send_safely(
        send_mail,
        f"[Oloustream] {contact.get_subject_display()} — {contact.full_name}",
        body,
        settings.DEFAULT_FROM_EMAIL,
        [settings.ADMIN_EMAIL],
    )


class AboutView(TemplateView):
    template_name = "user/about.html"


class RealisationsView(TemplateView):
    template_name = "user/realisations.html"


class LegalView(TemplateView):
    template_name = "front/legal.html"


class PrivacyView(TemplateView):
    template_name = "front/privacy.html"


@require_GET
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /dashboard/",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /messaging/",
        "Disallow: /notifications/",
        "Disallow: /fichiers/",
        "Disallow: /partenaires/dashboard/",
        "Disallow: /studio/my/",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")
