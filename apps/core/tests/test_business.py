from datetime import timedelta
from decimal import Decimal

from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.business_partners.models import BusinessPartner
from apps.business_partners.services import (
    PartnerActionError, activate_partner, cancel_contract, record_commission_payment, validate_contract,
)

from .factories import make_contract, make_partner, make_reservation, make_staff, make_studio, make_user


class ContractWorkflowTests(TestCase):
    def setUp(self):
        self.admin = make_staff("admin")
        self.partner = make_partner()

    def test_validation_counts_once(self):
        contract = make_contract(self.partner)
        validate_contract(contract, self.admin)
        with self.assertRaises(PartnerActionError):
            validate_contract(contract, self.admin)
        self.partner.refresh_from_db()
        self.assertEqual(self.partner.total_contracts, 1)
        self.assertEqual(self.partner.total_commission_earned, Decimal("200000.00"))

    def test_cancel_validated_contract_reverts_stats(self):
        contract = make_contract(self.partner)
        validate_contract(contract, self.admin)
        cancel_contract(contract, self.admin)
        self.partner.refresh_from_db()
        self.assertEqual(self.partner.total_contracts, 0)
        self.assertEqual(self.partner.total_revenue, Decimal("0"))

    def _earn(self, amount="1000000"):
        validate_contract(make_contract(self.partner, amount=Decimal(amount)), self.admin)

    def test_cannot_overpay(self):
        self._earn()  # 200 000 dus
        with self.assertRaises(PartnerActionError):
            record_commission_payment(self.partner, amount="250000", method="cash", admin_user=self.admin)

    def test_payment_is_not_double_counted(self):
        self._earn()
        record_commission_payment(self.partner, amount="50 000", method="cash", admin_user=self.admin)
        self.partner.refresh_from_db()
        self.assertEqual(self.partner.total_commission_paid, Decimal("50000.00"))

    def test_payment_rejects_invalid_amount(self):
        for bad in ("abc", "0", "-5"):
            with self.assertRaises(PartnerActionError):
                record_commission_payment(self.partner, amount=bad, method="cash", admin_user=self.admin)

    def test_payment_ignores_contracts_of_other_partner(self):
        self._earn()
        other = make_partner("autre")
        foreign = make_contract(other)
        payment = record_commission_payment(
            self.partner, amount="1000", method="cash", admin_user=self.admin, contract_ids=[foreign.pk],
        )
        self.assertEqual(payment.contracts.count(), 0)

    def test_validate_requires_post(self):
        contract = make_contract(self.partner)
        self.client.force_login(self.admin)
        url = reverse("dashboard:partner_contract_validate", args=[contract.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        contract.refresh_from_db()
        self.assertEqual(contract.status, "validated")


class PartnerActivationTests(TestCase):
    def test_activation_creates_account_and_sends_link(self):
        from apps.business_partners.models import PartnerApplication, Region
        region = Region.objects.create(name="Koudougou")
        application = PartnerApplication.objects.create(
            full_name="Awa Ouédraogo", phone="70", email="awa@example.com", id_number="X1", city=region,
            current_activity="x", network_description="x", sectors_knowledge="x", why_oloustream="x",
        )
        partner = activate_partner(application, make_staff("admin"))
        self.assertEqual(partner.partner_code, "BF-KOUD-001")
        self.assertFalse(partner.user.has_usable_password())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/reset/", mail.outbox[0].body + mail.outbox[0].alternatives[0][0])
        # Deuxième appel : idempotent
        self.assertEqual(activate_partner(application, make_staff("admin2")).pk, partner.pk)

    def test_suspended_partner_is_locked_out(self):
        partner = make_partner()
        partner.is_active = False
        partner.save()
        self.client.force_login(partner.user)
        self.assertEqual(self.client.get(reverse("partners:dashboard")).status_code, 302)


class ReservationConflictTests(TestCase):
    def setUp(self):
        self.admin = make_staff("admin")
        self.studio = make_studio()
        self.client_user = make_user()

    def test_cannot_confirm_overlapping_reservation(self):
        start = timezone.now() + timedelta(days=3)
        first = make_reservation(self.client_user, self.studio, start=start, status="CONFIRMED")
        second = make_reservation(make_user("bob"), self.studio, start=start + timedelta(hours=1))
        self.client.force_login(self.admin)
        self.client.post(reverse("dashboard:reservations_set_status", args=[second.pk]), {"status": "CONFIRMED"})
        second.refresh_from_db()
        self.assertEqual(second.status, "PENDING")
        self.assertEqual(first.status, "CONFIRMED")

    def test_open_redirect_is_blocked(self):
        reservation = make_reservation(self.client_user, self.studio)
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("dashboard:reservations_set_status", args=[reservation.pk]),
            {"status": "CANCELLED", "next": "https://site-malveillant.example/"},
        )
        self.assertEqual(response["Location"], reverse("dashboard:reservations_list"))


class ContactFormTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_contact_request_is_saved_and_team_notified(self):
        from apps.core.models import ContactRequest
        make_staff("admin")
        response = self.client.post(reverse("core:contact"), {
            "full_name": "Jean Client", "email": "jean@example.com", "subject": "LIVE",
            "message": "Nous souhaitons diffuser une conférence en direct.",
        })
        self.assertRedirects(response, reverse("core:contact"))
        self.assertEqual(ContactRequest.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_honeypot_blocks_bots(self):
        from apps.core.models import ContactRequest
        self.client.post(reverse("core:contact"), {
            "full_name": "Bot", "email": "bot@example.com", "subject": "OTHER",
            "message": "Spam spam spam spam", "website": "http://spam",
        })
        self.assertEqual(ContactRequest.objects.count(), 0)


class NumberToWordsTests(TestCase):
    def test_french_spelling(self):
        from apps.invoices.utils import number_to_words_french as words
        self.assertEqual(words(71), "soixante et onze")
        self.assertEqual(words(80), "quatre-vingts")
        self.assertEqual(words(280000), "deux cent quatre-vingt mille")
        self.assertEqual(words(1_250_000), "un million deux cent cinquante mille")
