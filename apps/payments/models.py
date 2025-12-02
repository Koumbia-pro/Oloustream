from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class PaymentMethod(models.TextChoices):
    ORANGE_MONEY = 'ORANGE_MONEY', 'Orange Money'
    MOOV_MONEY = 'MOOV_MONEY', 'Moov Money'


class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'En attente'
    PAID = 'PAID', 'Payé'
    FAILED = 'FAILED', 'Échoué'


class Payment(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name="Utilisateur",
    )
    reservation = models.ForeignKey(
        'studio.Reservation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name="Réservation liée",
    )
    amount = models.DecimalField("Montant", max_digits=10, decimal_places=2)
    method = models.CharField(
        "Méthode",
        max_length=20,
        choices=PaymentMethod.choices,
    )
    status = models.CharField(
        "Statut",
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    transaction_reference = models.CharField(
        "Référence transaction",
        max_length=100,
        blank=True,
    )
    created_at = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-created_at']

    def __str__(self):
        return f"Paiement #{self.id} - {self.amount} - {self.get_status_display()}"