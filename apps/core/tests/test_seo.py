from django.test import TestCase
from django.urls import reverse

from .factories import make_studio


class SitemapTests(TestCase):
    def test_sitemap_lists_public_pages_and_active_studios(self):
        active = make_studio("Studio Actif")
        hidden = make_studio("Studio Masqué")
        hidden.is_active = False
        hidden.save()

        response = self.client.get(reverse("core:sitemap"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        body = response.content.decode()
        self.assertIn(reverse("core:realisations"), body)
        self.assertIn(reverse("studio:user_studio_detail", args=[active.pk]), body)
        self.assertNotIn(reverse("studio:user_studio_detail", args=[hidden.pk]), body)
        self.assertNotIn("/dashboard/", body)

    def test_robots_txt_points_to_sitemap(self):
        response = self.client.get(reverse("core:robots"))
        self.assertIn("Sitemap: ", response.content.decode())
        self.assertIn("/sitemap.xml", response.content.decode())
