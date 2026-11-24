import io
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from apps.core.images import optimize_image_bytes
from apps.core.models import Testimonial
from apps.core.ratelimit import client_ip


def png_bytes(size=(3000, 2000), mode="RGB", color=(200, 30, 20)):
    buffer = io.BytesIO()
    Image.effect_noise(size, 60).convert(mode).save(buffer, "PNG") if mode == "RGB" else \
        Image.new(mode, size, color + (120,)).save(buffer, "PNG")
    return buffer.getvalue()


class ClientIpTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_vraie_adresse_derriere_cloudflare(self):
        request = self.factory.get("/", REMOTE_ADDR="172.70.1.10", HTTP_CF_CONNECTING_IP="41.138.5.9")
        self.assertEqual(client_ip(request), "41.138.5.9")

    def test_en_tete_ignore_hors_cloudflare(self):
        # Un client qui ne passe pas par Cloudflare ne peut pas choisir son adresse.
        request = self.factory.get("/", REMOTE_ADDR="41.138.5.9", HTTP_CF_CONNECTING_IP="1.2.3.4")
        self.assertEqual(client_ip(request), "41.138.5.9")

    def test_en_tete_invalide_ignore(self):
        request = self.factory.get("/", REMOTE_ADDR="172.70.1.10", HTTP_CF_CONNECTING_IP="pas-une-ip")
        self.assertEqual(client_ip(request), "172.70.1.10")


class AdminLoginTests(TestCase):
    def test_connexion_admin_passe_par_la_connexion_limitee(self):
        response = self.client.get("/admin/login/?next=/admin/")
        self.assertRedirects(response, reverse("accounts:login") + "?next=/admin/", fetch_redirect_response=False)


class ImageOptimizationTests(SimpleTestCase):
    def test_grande_photo_reduite_en_webp(self):
        result = optimize_image_bytes(png_bytes())
        self.assertIsNotNone(result)
        with Image.open(io.BytesIO(result)) as image:
            self.assertEqual(image.format, "WEBP")
            self.assertEqual(max(image.size), 1600)

    def test_transparence_conservee(self):
        result = optimize_image_bytes(png_bytes(size=(2400, 2400), mode="RGBA"))
        with Image.open(io.BytesIO(result)) as image:
            self.assertIn("A", image.mode)

    def test_fichier_non_image_ignore(self):
        self.assertIsNone(optimize_image_bytes(b"%PDF-1.4 pas une image"))


class UploadOptimizationTests(TestCase):
    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)

    def test_photo_envoyee_enregistree_en_webp(self):
        with override_settings(MEDIA_ROOT=self.media):
            testimonial = Testimonial.objects.create(
                quote="Super", author_role="Client",
                photo=SimpleUploadedFile("photo.png", png_bytes(), content_type="image/png"),
            )
            self.assertTrue(testimonial.photo.name.startswith("testimonials/"))
            self.assertTrue(testimonial.photo.name.endswith(".webp"))
            with Image.open(testimonial.photo.path) as image:
                self.assertLessEqual(max(image.size), 1600)


class PartnerCountersTests(TestCase):
    def test_compteurs_a_zero_masques(self):
        html = self.client.get(reverse("partners:program_info")).content.decode()
        self.assertNotIn("Partenaires actifs", html)


class AssetVersionTests(SimpleTestCase):
    def test_css_et_js_versionnes_par_leur_contenu(self):
        from apps.core.templatetags.assets import asset

        url = asset("css/site.css")
        self.assertRegex(url, r"^/static/css/site\.css\?v=[0-9a-f]{10}$")
        self.assertNotEqual(asset("css/site.css"), asset("js/site.js").replace("js/site.js", "css/site.css"))


class CssBundleTests(SimpleTestCase):
    def test_fichiers_css_regroupes_a_jour(self):
        from apps.core.cssbundle import BUNDLES, STATIC_DIR, build_bundle

        for bundle in BUNDLES:
            current = (STATIC_DIR / bundle).read_text(encoding="utf-8")
            self.assertEqual(current, build_bundle(bundle),
                             f"{bundle} n'est pas à jour : lancez « python manage.py build_css ».")


class HttpsUrlFieldTests(SimpleTestCase):
    """Un lien saisi sans protocole est complété en https:// (comportement de Django 6)."""

    def test_formulaire_partenaire(self):
        from apps.services_app.forms import PartnerForm
        field = PartnerForm.base_fields["website"]
        self.assertEqual(field.clean("oloustream.com"), "https://oloustream.com")

    def test_formulaire_profil(self):
        from apps.accounts.forms import EmployeeCreateForm
        field = EmployeeCreateForm.base_fields["linkedin_url"]
        self.assertEqual(field.clean("linkedin.com/in/test"), "https://linkedin.com/in/test")


class ContentSecurityPolicyTests(TestCase):
    def test_entete_et_nonce_de_la_page(self):
        import re
        response = self.client.get(reverse("core:home"))
        policy = response.headers["Content-Security-Policy"]
        self.assertIn("frame-ancestors 'none'", policy)
        self.assertIn("object-src 'none'", policy)
        nonce = re.search(r"'nonce-([^']+)'", policy).group(1)
        self.assertContains(response, f'<script nonce="{nonce}">')

    def test_nonce_change_a_chaque_page(self):
        first = self.client.get(reverse("core:home")).headers["Content-Security-Policy"]
        second = self.client.get(reverse("core:home")).headers["Content-Security-Policy"]
        self.assertNotEqual(first, second)

    def test_tous_les_scripts_integres_portent_le_nonce(self):
        """Garde-fou : un <script> écrit dans un gabarit sans nonce serait bloqué en ligne."""
        import re
        from pathlib import Path
        from django.conf import settings
        oublis = []
        for template in Path(settings.BASE_DIR, "templates").rglob("*.html"):
            for tag in re.findall(r"<script\b[^>]*>", template.read_text(encoding="utf-8")):
                if "src=" in tag or "nonce=" in tag or re.search(r'type="application/(ld\+)?json"', tag):
                    continue
                oublis.append(f"{template}: {tag}")
        self.assertEqual(oublis, [], "Ajoutez nonce=\"{{ csp_nonce }}\" à ces balises <script>")
