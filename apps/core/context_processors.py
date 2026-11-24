from urllib.parse import quote

from django.conf import settings

WHATSAPP_NUMBER = "22664093196"

WHATSAPP_DEFAULT_MESSAGE = (
    "Bonjour Oloustream 👋\n"
    "Je viens de votre site et je souhaite des informations sur vos services.\n"
    "Mon projet en quelques mots : …\n"
    "Merci de me recontacter dès que possible."
)

# Message pré-rempli selon la page visitée (nom d'URL complet -> message)
WHATSAPP_PAGE_MESSAGES = {
    "studio:user_studio_list": (
        "Bonjour l'équipe Oloustream 🎙️\n"
        "Vos studios ont retenu mon attention. J'aimerais connaître leurs disponibilités "
        "et leurs tarifs pour le … Merci !"
    ),
    "studio:user_equipment_list": (
        "Bonjour l'équipe Oloustream 🎥\n"
        "Je souhaite louer du matériel pour un tournage. Voici ce dont j'ai besoin : …\n"
        "Pouvez-vous me faire une proposition ?"
    ),
    "services_app:user_trainings_list": (
        "Bonjour l'équipe Oloustream 🎓\n"
        "Vos formations m'intéressent beaucoup ! J'aimerais connaître les prochaines dates "
        "et les modalités d'inscription."
    ),
    "core:realisations": (
        "Bonjour l'équipe Oloustream 🎬\n"
        "J'ai adoré vos réalisations ! J'aimerais un devis pour un projet du même type : …"
    ),
}
WHATSAPP_PAGE_MESSAGES["studio:user_equipment_detail"] = WHATSAPP_PAGE_MESSAGES["studio:user_equipment_list"]


def whatsapp_message_for(request):
    """Choisit le message WhatsApp pré-rempli adapté à la page visitée."""
    match = getattr(request, "resolver_match", None)
    view_name = match.view_name if match else ""
    if view_name == "studio:user_studio_detail":
        from apps.studio.models import Studio

        name = Studio.objects.filter(pk=match.kwargs.get("pk"), is_active=True).values_list("name", flat=True).first()
        if name:
            return (
                "Bonjour l'équipe Oloustream 🎙️\n"
                f"Le {name} a retenu mon attention. J'aimerais connaître ses disponibilités "
                "et ses tarifs pour le … Merci !"
            )
    return WHATSAPP_PAGE_MESSAGES.get(view_name, WHATSAPP_DEFAULT_MESSAGE)


def site_settings(request):
    """Informations de contact et liens utilisés dans tous les gabarits."""
    return {
        "SITE": {
            "name": "Oloustream",
            "tagline": "Studios, production audiovisuelle et live streaming",
            "email": "info@oloustream.com",
            "phone": "+226 64 09 31 96",
            "phone_link": "+22664093196",
            "phone_2": "+226 25 65 53 95",
            "phone_2_link": "+22625655395",
            "whatsapp": f"https://wa.me/{WHATSAPP_NUMBER}",
            "address_lines": ["Secteur 15, Ouaga 2000", "Parcelle 10, Lot 01", "Ouagadougou, Burkina Faso"],
            "facebook": "https://www.facebook.com/oloustream",
            "instagram": "https://www.instagram.com/oloustream",
            "youtube": "https://www.youtube.com/@Oloustream",
            "linkedin": "https://www.linkedin.com/company/oloustream",
        },
        "SITE_URL": settings.SITE_URL,
        "WHATSAPP_URL": f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(whatsapp_message_for(request))}",
    }


def partner_counts(request):
    """Compteurs affichés dans la barre latérale et l'en-tête du dashboard."""
    user = getattr(request, "user", None)
    if not (user and user.is_authenticated and user.is_staff):
        return {}

    from apps.business_partners.models import Contract, PartnerApplication
    from apps.notifications.models import Notification, NotificationTypeChoices
    from apps.studio.models import Reservation

    from .models import ContactRequest
    from .permissions import is_team_admin

    unread = Notification.objects.filter(user=user, is_read=False)
    return {
        "is_team_admin": is_team_admin(user),
        "new_contacts_count": ContactRequest.objects.filter(status=ContactRequest.Status.NEW).count(),
        "pending_reservations_count": Reservation.objects.filter(status="PENDING").count(),
        "pending_applications_count": PartnerApplication.objects.filter(status="pending").count(),
        "pending_contracts_count": Contract.objects.filter(status="pending").count(),
        "unread_notifications_count": unread.count(),
        "unread_messages_count": unread.filter(
            notification_type=NotificationTypeChoices.MESSAGE_RECEIVED
        ).count(),
    }
