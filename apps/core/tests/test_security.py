from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from .factories import make_partner, make_staff, make_user


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class LoginRateLimitTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user("alice")

    def test_blocks_after_too_many_failures(self):
        url = reverse("accounts:login")
        for _ in range(5):
            self.client.post(url, {"username": "alice", "password": "mauvais"})
        response = self.client.post(url, {"username": "alice", "password": "Motdepasse!2026"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Trop de tentatives")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_with_email(self):
        response = self.client.post(reverse("accounts:login"), {"username": "alice@example.com", "password": "Motdepasse!2026"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)


class LogoutTests(TestCase):
    def test_logout_requires_post(self):
        self.client.force_login(make_user())
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        self.client.post(reverse("accounts:logout"))
        self.assertNotIn("_auth_user_id", self.client.session)


class DashboardAccessTests(TestCase):
    def test_client_cannot_open_dashboard(self):
        self.client.force_login(make_user())
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_technician_cannot_manage_team(self):
        self.client.force_login(make_staff("tech", role="TECHNICIAN"))
        self.assertEqual(self.client.get(reverse("dashboard:employees_list")).status_code, 403)

    def test_manager_cannot_touch_superuser(self):
        manager = make_staff("boss", role="MANAGER")
        root = make_user("root", is_superuser=True, is_staff=True, is_employee=True)
        self.client.force_login(manager)
        url = reverse("dashboard:employees_change_password", args=[root.pk])
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_manager_cannot_grant_superadmin(self):
        from apps.accounts.forms import EmployeeCreateForm
        manager = make_staff("boss", role="MANAGER")
        form = EmployeeCreateForm(acting_user=manager)
        self.assertNotIn("SUPERADMIN", [value for value, _ in form.fields["role"].choices])


class ProtectedFileTests(TestCase):
    def test_other_partner_cannot_download_contract(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .factories import make_contract

        owner = make_partner("owner")
        contract = make_contract(owner)
        contract.contract_file.save("c.pdf", SimpleUploadedFile("c.pdf", b"%PDF-1.4 test"), save=True)
        url = reverse("core:protected_file", args=["contrat-partenaire", contract.pk])

        self.client.force_login(make_partner("intrus").user)
        self.assertEqual(self.client.get(url).status_code, 404)

        self.client.force_login(owner.user)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_anonymous_redirected_to_login(self):
        url = reverse("core:protected_file", args=["piece-identite", 1])
        self.assertEqual(self.client.get(url).status_code, 302)


class UploadValidationTests(TestCase):
    def test_rejects_fake_pdf(self):
        from django.core.exceptions import ValidationError
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.core.validators import validate_document

        with self.assertRaises(ValidationError):
            validate_document(SimpleUploadedFile("cv.pdf", b"<html>pas un pdf</html>"))
        with self.assertRaises(ValidationError):
            validate_document(SimpleUploadedFile("page.html", b"<html></html>"))
        validate_document(SimpleUploadedFile("ok.pdf", b"%PDF-1.7 contenu"))


class ExcelInjectionTests(TestCase):
    def test_formula_is_neutralised(self):
        from apps.core.utils import _excel_safe
        self.assertEqual(_excel_safe("=HYPERLINK(\"x\")"), "'=HYPERLINK(\"x\")")
        self.assertEqual(_excel_safe("Nom normal"), "Nom normal")
        self.assertEqual(_excel_safe(12), 12)
