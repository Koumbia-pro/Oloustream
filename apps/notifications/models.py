from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = settings.AUTH_USER_MODEL


class NotificationTypeChoices(models.TextChoices):
    GENERAL = 'GENERAL', 'Générale'
    RESERVATION_CREATED = 'RESERVATION_CREATED', 'Nouvelle réservation'
    RESERVATION_STATUS_CHANGED = 'RESERVATION_STATUS_CHANGED', 'Changement de statut de réservation'
    MESSAGE_RECEIVED = 'MESSAGE_RECEIVED', 'Nouveau message'
    PAYMENT_STATUS = 'PAYMENT_STATUS', 'Mise à jour paiement'
    SYSTEM = 'SYSTEM', 'Notification système'


class Notification(models.Model):
    # Destinataire
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Destinataire",
    )

    # Acteur (optionnel)
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications_sent',
        verbose_name="Acteur",
    )

    # Type
    notification_type = models.CharField(
        "Type de notification",
        max_length=50,
        choices=NotificationTypeChoices.choices,
        default=NotificationTypeChoices.GENERAL,
    )

    # Contenu
    title = models.CharField("Titre", max_length=200)
    message = models.TextField("Message")

    # Lien générique vers un objet (réservation, message, paiement, etc.)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target_object = GenericForeignKey('content_type', 'object_id')

    # Statut de lecture
    is_read = models.BooleanField("Lue", default=False)
    read_at = models.DateTimeField("Lue le", null=True, blank=True)

    # Lien optionnel (URL)
    link = models.CharField("Lien (URL interne)", max_length=255, blank=True)

    # Dates
    created_at = models.DateTimeField("Créée le", auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"Notif pour {self.user} : {self.title}"