"""Logique métier du programme de partenaires d'affaires."""
import secrets
from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, F, Q, Sum
from django.utils import timezone
from django.utils.text import slugify

from .models import BusinessPartner, CommissionPayment, Contract

User = get_user_model()


class PartnerActionError(Exception):
    """Action impossible sur un partenaire / contrat (message affichable)."""


# ---------- Activation ----------

def generate_partner_code(city_name):
    """Génère un code partenaire unique : BF-CITY-XXX"""
    city_code = (slugify(city_name or "")[:4] or "BF").upper()
    prefix = f"BF-{city_code}-"
    existing = BusinessPartner.objects.filter(partner_code__startswith=prefix).values_list("partner_code", flat=True)
    numbers = [int(code.rsplit("-", 1)[-1]) for code in existing if code.rsplit("-", 1)[-1].isdigit()]
    return f"{prefix}{(max(numbers, default=0) + 1):03d}"


def _unique_username(full_name):
    base = slugify(full_name).replace("-", ".")[:30] or "partenaire"
    username = base
    while User.objects.filter(username=username).exists():
        username = f"{base}.{secrets.randbelow(9000) + 1000}"
    return username


def activate_partner(application, admin_user):
    """
    Active un partenaire après approbation de sa candidature :
    crée (ou réutilise) le compte utilisateur et le profil BusinessPartner,
    puis envoie un lien sécurisé pour définir son mot de passe.
    """
    existing = BusinessPartner.objects.filter(application=application).first()
    if existing:
        return existing
    if not application.email:
        raise PartnerActionError("La candidature n'a pas d'email : impossible de créer l'accès partenaire.")

    with transaction.atomic():
        user = User.objects.filter(email__iexact=application.email).first()
        if user is None:
            names = application.full_name.split()
            user = User.objects.create_user(
                username=_unique_username(application.full_name),
                email=application.email,
                password=None,  # le partenaire définit lui-même son mot de passe
                first_name=names[0] if names else "",
                last_name=" ".join(names[1:]),
                phone=application.phone,
            )
        elif BusinessPartner.objects.filter(user=user).exists():
            raise PartnerActionError("Un partenaire est déjà associé au compte de cet email.")

        city_name = application.city.name if application.city else ""
        for _ in range(5):
            try:
                with transaction.atomic():
                    partner = BusinessPartner.objects.create(
                        application=application,
                        user=user,
                        partner_code=generate_partner_code(city_name),
                        commission_rate=Decimal("20.00"),
                        is_active=True,
                    )
                break
            except IntegrityError:
                continue
        else:
            raise PartnerActionError("Impossible de générer un code partenaire unique. Réessayez.")

        application.status = "approved"
        application.reviewed_by = admin_user
        application.reviewed_at = timezone.now()
        application.save(update_fields=["status", "reviewed_by", "reviewed_at", "updated_at"])

    from apps.notifications.emailing import send_partner_activation_email
    from apps.core.utils import send_safely
    send_safely(send_partner_activation_email, partner)
    return partner


# ---------- Contrats ----------

def validate_contract(contract, admin_user):
    """Valide un contrat en attente et crédite les statistiques du partenaire (une seule fois)."""
    with transaction.atomic():
        contract = Contract.objects.select_for_update().get(pk=contract.pk)
        if contract.status != "pending":
            raise PartnerActionError("Seul un contrat en attente peut être validé.")
        now = timezone.now()
        contract.status = "validated"
        contract.validated_by = admin_user
        contract.validated_at = now
        contract.save(update_fields=["status", "validated_by", "validated_at"])

        BusinessPartner.objects.filter(pk=contract.partner_id).update(
            total_contracts=F("total_contracts") + 1,
            total_revenue=F("total_revenue") + contract.contract_amount,
            total_commission_earned=F("total_commission_earned") + contract.commission_amount,
            last_contract_at=now,
        )

    from apps.notifications.services import notify_contract_validated
    notify_contract_validated(contract)
    return contract


def cancel_contract(contract, admin_user=None):
    """Annule un contrat. S'il avait été validé, retire son montant des statistiques du partenaire."""
    with transaction.atomic():
        contract = Contract.objects.select_for_update().get(pk=contract.pk)
        if contract.status in {"cancelled", "completed"}:
            raise PartnerActionError("Ce contrat ne peut plus être annulé.")
        was_counted = contract.status in {"validated", "signed", "in_progress"}
        contract.status = "cancelled"
        contract.save(update_fields=["status"])
        if was_counted:
            BusinessPartner.objects.filter(pk=contract.partner_id).update(
                total_contracts=F("total_contracts") - 1,
                total_revenue=F("total_revenue") - contract.contract_amount,
                total_commission_earned=F("total_commission_earned") - contract.commission_amount,
            )
    return contract


# ---------- Paiements ----------

def parse_amount(raw):
    try:
        amount = Decimal(str(raw).replace(" ", "").replace(",", "."))
    except (InvalidOperation, TypeError):
        raise PartnerActionError("Montant invalide.")
    if amount <= 0:
        raise PartnerActionError("Le montant doit être supérieur à 0.")
    return amount.quantize(Decimal("0.01"))


def record_commission_payment(partner, *, amount, method, admin_user, reference="", notes="",
                              contract_ids=None, receipt=None):
    """Enregistre un versement de commission et met à jour le total versé (une seule fois)."""
    amount = parse_amount(amount)
    if method not in dict(CommissionPayment.PAYMENT_METHODS):
        raise PartnerActionError("Méthode de paiement invalide.")

    with transaction.atomic():
        payment = CommissionPayment.objects.create(
            partner=partner,
            amount=amount,
            payment_method=method,
            reference=reference[:100],
            notes=notes,
            receipt=receipt or "",
            created_by=admin_user,
        )
        if contract_ids:
            contracts = Contract.objects.filter(partner=partner, pk__in=contract_ids)
            payment.contracts.set(contracts)
        BusinessPartner.objects.filter(pk=partner.pk).update(
            total_commission_paid=F("total_commission_paid") + amount
        )
    return payment


# ---------- Statistiques ----------

def calculate_partner_performance(partner):
    """Calcule les performances d'un partenaire"""
    return Contract.objects.filter(partner=partner).aggregate(
        total_contracts=Count("id"),
        total_amount=Sum("contract_amount"),
        total_commission=Sum("commission_amount"),
        avg_contract_value=Avg("contract_amount"),
        completed=Count("id", filter=Q(status="completed")),
        pending=Count("id", filter=Q(status="pending")),
    )


def get_top_partners(limit=10):
    """Retourne les meilleurs partenaires par CA généré"""
    return BusinessPartner.objects.filter(is_active=True).select_related("user").order_by("-total_revenue")[:limit]
