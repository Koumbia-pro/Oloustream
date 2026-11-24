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
