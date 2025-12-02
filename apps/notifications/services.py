from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.conf import settings

from .models import Notification, NotificationTypeChoices
from apps.accounts.models import User
from apps.messaging.models import Conversation, Message

UserModel = User  # pour clarté


def create_notification(
    *,
    user: UserModel,
    title: str,
    message: str,
    notification_type: str = NotificationTypeChoices.GENERAL,
    actor: UserModel = None,
    target_object=None,
    link: str = "",
) -> Notification:
    """
    Crée une notification générique pour un utilisateur.
    """
    content_type = None
    object_id = None
    if target_object is not None:
        content_type = ContentType.objects.get_for_model(target_object.__class__)
        object_id = target_object.pk

    notif = Notification.objects.create(
        user=user,
        actor=actor,
        notification_type=notification_type,
        title=title,
        message=message,
        content_type=content_type,
        object_id=object_id,
        link=link or "",
    )
    return notif


def mark_notification_as_read(notification: Notification):
    """
    Marque une notification comme lue.
    """
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['is_read', 'read_at'])


def mark_all_notifications_as_read(user: UserModel):
    """
    Marque toutes les notifications d'un utilisateur comme lues.
    """
    qs = Notification.objects.filter(user=user, is_read=False)
    now = timezone.now()
    qs.update(is_read=True, read_at=now)


# ==== EXEMPLES SPÉCIFIQUES POUR RÉSERVATIONS ==== #

def notify_admins_new_reservation(reservation):
    """
    Notifie les admins / staff d'une nouvelle réservation créée par un utilisateur.
    """
    admins = UserModel.objects.filter(is_staff=True)
    title = f"Nouvelle réservation #{reservation.id}"
    message = (
        f"L'utilisateur {reservation.user.get_full_name() or reservation.user.username} "
        f"a créé une nouvelle réservation pour le service "
        f"'{reservation.service.name if reservation.service else '-'}'."
    )
    link = f"/dashboard/reservations/{reservation.id}/"

    for admin in admins:
        create_notification(
            user=admin,
            actor=reservation.user,
            title=title,
            message=message,
            notification_type=NotificationTypeChoices.RESERVATION_CREATED,
            target_object=reservation,
            link=link,
        )


def notify_user_reservation_status_change(reservation, old_status, new_status, actor=None):
    """
    Notifie le client qu'un statut de réservation a changé.
    """
    title = f"Mise à jour de votre réservation #{reservation.id}"
    message = (
        f"Le statut de votre réservation pour le service "
        f"'{reservation.service.name if reservation.service else '-'}' a changé : "
        f"'{old_status}' → '{new_status}'."
    )
    link = f"/studio/my/reservations/"

    create_notification(
        user=reservation.user,
        actor=actor,
        title=title,
        message=message,
        notification_type=NotificationTypeChoices.RESERVATION_STATUS_CHANGED,
        target_object=reservation,
        link=link,
    )


from apps.messaging.models import Conversation, Message


def notify_new_chat_message(message: Message):
    """
    Crée une notification lors d'un nouveau message dans une conversation.
    - Si le message vient de l'utilisateur (conversation.user) -> notifie admin(s)
    - Si le message vient d'un admin/staff                 -> notifie l'utilisateur
    """
    conversation = message.conversation
    sender = message.sender

    # Si c'est l'utilisateur qui envoie (côté client)
    if sender == conversation.user:
        # Destinataires : admin assigné à la conversation, sinon tous les staff
        recipients = []
        if conversation.admin and conversation.admin.is_active:
            recipients.append(conversation.admin)
        else:
            recipients = list(User.objects.filter(is_staff=True, is_active=True))

        title = f"Nouveau message de {sender.get_full_name() or sender.username}"
        preview = (message.content[:120] + "…") if len(message.content) > 120 else message.content
        link = f"/messaging/admin/conversations/{conversation.id}/"

        for admin in recipients:
            create_notification(
                user=admin,
                actor=sender,
                title=title,
                message=preview,
                notification_type=NotificationTypeChoices.MESSAGE_RECEIVED,
                target_object=conversation,
                link=link,
            )

    else:
        # Sinon, on suppose que c'est un admin/staff qui répond -> notifier l'utilisateur
        title = "Nouvelle réponse de l'équipe Oloustream"
        preview = (message.content[:120] + "…") if len(message.content) > 120 else message.content
        link = "/messaging/chat/"

        create_notification(
            user=conversation.user,
            actor=sender,
            title=title,
            message=preview,
            notification_type=NotificationTypeChoices.MESSAGE_RECEIVED,
            target_object=conversation,
            link=link,
        )



def notify_admins_new_service(service):
    admins = UserModel.objects.filter(is_staff=True, is_active=True)
    title = f"Nouveau service créé : {service.name}"
    message = (service.short_description or "")[:200]
    link = f"/dashboard/services/{service.id}/"
    for admin in admins:
        create_notification(
            user=admin,
            actor=None,
            title=title,
            message=message,
            notification_type=NotificationTypeChoices.SYSTEM,
            target_object=service,
            link=link,
        )


def notify_users_new_training_session(training, users_qs):
    title = f"Nouvelle session de formation : {training.title}"
    message = f"La formation '{training.title}' est désormais disponible."
    link = f"/services/trainings/"  # ou une page vitrine à venir

    for user in users_qs:
        create_notification(
            user=user,
            actor=None,
            title=title,
            message=message,
            notification_type=NotificationTypeChoices.GENERAL,
            target_object=training,
            link=link,
        )