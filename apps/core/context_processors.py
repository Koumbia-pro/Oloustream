from django.conf import settings


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
            "whatsapp": "https://wa.me/22664093196",
            "address_lines": ["Secteur 15, Ouaga 2000", "Parcelle 10, Lot 01", "Ouagadougou, Burkina Faso"],
            "facebook": "https://www.facebook.com/oloustream",
            "instagram": "https://www.instagram.com/oloustream",
            "youtube": "https://www.youtube.com/@Oloustream",
            "linkedin": "https://www.linkedin.com/company/oloustream",
        },
        "SITE_URL": settings.SITE_URL,
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
