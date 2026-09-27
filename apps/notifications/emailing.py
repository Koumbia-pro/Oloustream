"""
Envoi des emails transactionnels d'Oloustream.

Chaque fonction peut lever une exception SMTP : les vues les appellent
via `apps.core.utils.send_safely` pour ne jamais bloquer l'utilisateur.
"""
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode


def _absolute(path):
    return f"{settings.SITE_URL}{path}"


def _send(subject, template, context, to, text_body=None):
    recipients = [email for email in to if email]
    if not recipients:
        return False
    context = {"site_url": settings.SITE_URL, **context}
    html = render_to_string(template, context)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body or strip_tags(html),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=False)
    return True


# ---------- Réservations ----------

def send_reservation_received_email(request, reservation):
    user = reservation.user
    return _send(
        f"Oloustream – Demande reçue (réservation #{reservation.id})",
        "emails/reservation_received.html",
        {
            "reservation_id": reservation.id,
            "user_name": user.get_full_name() or user.username,
            "start": reservation.start_datetime,
            "end": reservation.end_datetime,
            "studio_name": reservation.studio.name if reservation.studio else "",
            "status_label": reservation.get_status_display(),
            "reservations_url": _absolute(reverse("studio:user_reservations_list")),
        },
        [reservation.contact_email or user.email],
        text_body="Votre demande de réservation a bien été reçue. Notre équipe revient vers vous rapidement.",
    )


def send_reservation_status_changed_email(request, reservation, old_status_label, new_status_label, admin_note=""):
    user = reservation.user
    return _send(
        f"Oloustream – Réservation #{reservation.id} : {new_status_label}",
        "emails/reservation_status_changed.html",
        {
            "reservation_id": reservation.id,
            "user_name": user.get_full_name() or user.username,
            "old_status": old_status_label,
            "new_status": new_status_label,
            "start": reservation.start_datetime,
            "end": reservation.end_datetime,
            "studio_name": reservation.studio.name if reservation.studio else "",
            "admin_note": admin_note,
            "user_reservations_url": _absolute(reverse("studio:user_reservations_list")),
        },
        [reservation.contact_email or user.email],
        text_body=f"Statut de votre réservation #{reservation.id} : {old_status_label} → {new_status_label}.",
    )


# ---------- Recrutement ----------

def send_job_application_confirmation(application):
    return _send(
        "Oloustream – Confirmation de votre candidature",
        "emails/job_application_confirmation.html",
        {"full_name": application.full_name, "offer": application.offer},
        [application.email],
    )


# ---------- Partenaires d'affaires ----------

def send_partner_application_notification(application):
    """Notifie l'équipe d'une nouvelle candidature partenaire."""
    url = _absolute(reverse("dashboard:partner_application_detail", args=[application.id]))
    msg = EmailMultiAlternatives(
        subject=f"[Oloustream] Nouvelle candidature partenaire – {application.full_name}",
        body=(
            "Nouvelle candidature partenaire reçue :\n\n"
            f"Nom : {application.full_name}\n"
            f"Ville : {application.city or '-'}\n"
            f"Téléphone : {application.phone}\n"
            f"Email : {application.email or '-'}\n"
            f"Réseau : {application.get_network_strength_display()}\n\n"
            f"Voir la candidature : {url}\n"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.ADMIN_EMAIL],
    )
    msg.send(fail_silently=False)
    return True


def send_partner_activation_email(partner):
    """Envoie au nouveau partenaire un lien sécurisé pour définir son mot de passe."""
    user = partner.user
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return _send(
        f"Bienvenue chez Oloustream – Votre code partenaire : {partner.partner_code}",
        "emails/partner_activation.html",
        {
            "partner": partner,
            "username": user.username,
            "set_password_url": _absolute(reverse("password_reset_confirm", args=[uid, token])),
            "login_url": _absolute(reverse("accounts:login")),
            "dashboard_url": _absolute(reverse("partners:dashboard")),
        },
        [user.email],
    )


def send_contract_validated_email(contract):
    """Informe le partenaire qu'un de ses contrats est validé."""
    partner_user = contract.partner.user
    return _send(
        f"Oloustream – Contrat validé : commission de {contract.commission_amount:,.0f} FCFA".replace(",", " "),
        "emails/contract_validated.html",
        {
            "contract": contract,
            "partner_name": partner_user.get_full_name() or partner_user.username,
            "contract_url": _absolute(reverse("partners:contract_detail", args=[contract.pk])),
        },
        [partner_user.email],
    )
