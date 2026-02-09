from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Contract, BusinessPartner, CommissionPayment


@receiver(post_save, sender=Contract)
def update_partner_stats_on_contract_validation(sender, instance, created, **kwargs):
    """
    Met à jour les statistiques du partenaire quand un contrat change de statut
    """
    if not created and instance.status == 'validated':
        partner = instance.partner
        
        # Vérifier si c'est la première validation (pas déjà comptabilisé)
        if instance.validated_at and not instance._state.adding:
            # Les stats sont déjà mises à jour dans la vue admin
            # Ce signal peut servir pour d'autres actions
            pass


@receiver(post_save, sender=CommissionPayment)
def update_partner_paid_commission(sender, instance, created, **kwargs):
    """
    Met à jour le montant total versé au partenaire
    """
    if created:
        partner = instance.partner
        partner.total_commission_paid += instance.amount
        partner.save(update_fields=['total_commission_paid'])