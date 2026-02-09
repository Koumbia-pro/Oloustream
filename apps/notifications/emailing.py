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




# AJOUTER ces fonctions dans ton fichier emailing.py existant
#==================================================== pour la partie business partners ====================================
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def send_partner_application_notification(application):
    """Notifie l'équipe d'une nouvelle candidature partenaire"""
    subject = f"🤝 Nouvelle candidature partenaire - {application.full_name}"
    
    message = f"""
    Nouvelle candidature partenaire reçue :
    
    Nom : {application.full_name}
    Ville : {application.city}
    Téléphone : {application.phone}
    Réseau : {application.get_network_strength_display()}
    
    👉 Voir la candidature : {settings.SITE_URL}/admin/partners/applications/{application.id}/
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [settings.ADMIN_EMAIL],  # À définir dans settings.py
        fail_silently=True,
    )


def send_partner_activation_email(partner, password):
    """Envoie les identifiants au nouveau partenaire"""
    subject = f"🎉 Bienvenue chez Oloustream - Votre code partenaire : {partner.partner_code}"
    
    context = {
        'partner': partner,
        'password': password,
        'login_url': f"{settings.SITE_URL}/partners/login/",
    }
    
    html_message = render_to_string('emails/partner_activation.html', context)
    
    send_mail(
        subject,
        f"Votre code partenaire : {partner.partner_code}\nMot de passe : {password}",
        settings.DEFAULT_FROM_EMAIL,
        [partner.user.email],
        html_message=html_message,
        fail_silently=False,
    )


def notify_contract_validated(contract):
    """Notifie le partenaire qu'un contrat est validé"""
    subject = f"✅ Contrat validé - Commission : {contract.commission_amount:,.0f} FCFA"
    
    message = f"""
    Félicitations {contract.partner.user.get_full_name()} !
    
    Votre contrat a été validé :
    
    Client : {contract.client_name}
    Montant : {contract.contract_amount:,.0f} FCFA
    Commission : {contract.commission_amount:,.0f} FCFA ({contract.commission_rate}%)
    
    Votre commission sera versée prochainement.
    
    Merci pour votre collaboration !
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [contract.partner.user.email],
        fail_silently=True,
    )