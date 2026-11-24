from django.test import TestCase
from django.urls import reverse

from apps.core.models import Testimonial

from .factories import make_staff, make_user


class TestimonialTests(TestCase):
    def setUp(self):
        Testimonial.objects.all().delete()

    def test_accueil_affiche_seulement_les_temoignages_publies(self):
        Testimonial.objects.create(quote="Équipe formidable", author_name="Awa Ouédraogo",
                                   author_role="Directrice", organization="ONG Lumière")
        Testimonial.objects.create(quote="Brouillon secret", author_role="Client", is_published=False)
        html = self.client.get(reverse("core:home")).content.decode()
        self.assertIn("Équipe formidable", html)
        self.assertIn("Awa Ouédraogo", html)
        self.assertIn("Directrice, ONG Lumière", html)
        self.assertNotIn("Brouillon secret", html)

    def test_section_masquee_sans_temoignage(self):
        html = self.client.get(reverse("core:home")).content.decode()
        self.assertNotIn("fa-quote-left", html)

    def test_gestion_depuis_le_tableau_de_bord(self):
        self.client.force_login(make_user("visiteur"))
        self.assertNotEqual(self.client.get(reverse("dashboard:testimonials_list")).status_code, 200)

        self.client.force_login(make_staff("equipe", role="ADMIN"))
        self.assertEqual(self.client.get(reverse("dashboard:testimonials_create")).status_code, 200)
        response = self.client.post(reverse("dashboard:testimonials_create"), {
            "quote": "Un travail remarquable.", "author_role": "Chargé de communication",
            "organization": "Mairie", "is_published": "on", "order": 1,
        })
        self.assertRedirects(response, reverse("dashboard:testimonials_list"))
        testimonial = Testimonial.objects.get()
        self.assertContains(self.client.get(reverse("dashboard:testimonials_list")), "Un travail remarquable.")

        self.client.post(reverse("dashboard:testimonials_toggle", args=[testimonial.pk]))
        testimonial.refresh_from_db()
        self.assertFalse(testimonial.is_published)

        self.assertEqual(self.client.get(reverse("dashboard:testimonials_edit", args=[testimonial.pk])).status_code, 200)
        self.client.post(reverse("dashboard:testimonials_delete", args=[testimonial.pk]))
        self.assertFalse(Testimonial.objects.exists())
