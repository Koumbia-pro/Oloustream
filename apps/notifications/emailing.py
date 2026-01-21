from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse


def send_reservation_received_email(request, reservation):
    user = reservation.user
    if not user.email:
        return

    subject = f"Oloustream – Demande reçue (Réservation #{reservation.id})"
    html = render_to_string("emails/reservation_received.html", {
        "reservation_id": reservation.id,
        "user_name": user.get_full_name() or user.username,
        "start": reservation.start_datetime,
        "end": reservation.end_datetime,
        "studio_name": reservation.studio.name if reservation.studio else "",
        "status_label": reservation.get_status_display(),
    })

    msg = EmailMultiAlternatives(
        subject=subject,
        body="Votre demande de réservation a bien été reçue.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=False)


def send_reservation_status_changed_email(request, reservation, old_status_label, new_status_label, admin_note=""):
    user = reservation.user
    if not user.email:
        return

    subject = f"Oloustream – Mise à jour réservation #{reservation.id} ({new_status_label})"
    user_reservations_url = request.build_absolute_uri(reverse("studio:user_reservations_list"))

    html = render_to_string("emails/reservation_status_changed.html", {
        "reservation_id": reservation.id,
        "user_name": user.get_full_name() or user.username,
        "old_status": old_status_label,
        "new_status": new_status_label,
        "start": reservation.start_datetime,
        "end": reservation.end_datetime,
        "studio_name": reservation.studio.name if reservation.studio else "",
        "admin_note": admin_note,
        "user_reservations_url": user_reservations_url,
    })

    msg = EmailMultiAlternatives(
        subject=subject,
        body=f"Statut mis à jour : {old_status_label} -> {new_status_label}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=False)