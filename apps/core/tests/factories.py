"""Petites fabriques d'objets pour les tests."""
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from apps.accounts.models import User


def make_user(username="client", **extra):
    defaults = {"email": f"{username}@example.com", "password": "Motdepasse!2026"}
    defaults.update(extra)
    password = defaults.pop("password")
    return User.objects.create_user(username=username, password=password, **defaults)


def make_staff(username="staff", role="TECHNICIAN", **extra):
    return make_user(username, is_staff=True, is_employee=True, role=role, **extra)


def make_studio(name="Studio A"):
    from apps.studio.models import Studio
    return Studio.objects.create(name=name)


def make_reservation(user, studio, start=None, hours=2, status="PENDING"):
    from apps.studio.models import Reservation
    start = start or timezone.now() + timedelta(days=2)
    return Reservation.objects.create(
        user=user, studio=studio, start_datetime=start, end_datetime=start + timedelta(hours=hours), status=status,
    )


def make_partner(username="partner", amount_rate=Decimal("20")):
    from apps.business_partners.models import BusinessPartner, PartnerApplication, Region
    region, _ = Region.objects.get_or_create(name="Bobo-Dioulasso")
    user = make_user(username)
    application = PartnerApplication.objects.create(
        full_name="Paul Partner", phone="70000000", email=user.email, id_number="B123", city=region,
        current_activity="Commercial", network_description="Réseau", sectors_knowledge="ONG",
        why_oloustream="Motivation",
    )
    return BusinessPartner.objects.create(
        application=application, user=user, partner_code=f"BF-TEST-{user.pk:03d}", commission_rate=amount_rate,
    )


def make_contract(partner, amount=Decimal("1000000"), status="pending"):
    from apps.business_partners.models import Contract
    return Contract.objects.create(
        partner=partner, client_name="ONG X", client_type="ong", client_contact="+226", service_type="Live",
        description="Captation", contract_amount=amount, commission_rate=partner.commission_rate, status=status,
    )
