from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from apps.core.models import VideoRealisation
from apps.core.utils import youtube_id_from_url


class YoutubeIdTests(SimpleTestCase):
    def test_reconnait_les_formats_de_lien(self):
        for url in [
            "https://youtu.be/mDGgGi5hjFI?si=ria6pDd9KkK_dGZ4",
            "https://www.youtube.com/watch?v=mDGgGi5hjFI&t=30s",
            "youtube.com/watch?v=mDGgGi5hjFI",
            "https://m.youtube.com/watch?v=mDGgGi5hjFI",
            "https://www.youtube.com/shorts/mDGgGi5hjFI",
            "https://www.youtube.com/embed/mDGgGi5hjFI",
            "mDGgGi5hjFI",
        ]:
            self.assertEqual(youtube_id_from_url(url), "mDGgGi5hjFI", url)

    def test_refuse_les_liens_inconnus(self):
        for url in ["", "https://vimeo.com/123", "https://evil.com/watch?v=mDGgGi5hjFI", "https://youtu.be/<script>"]:
            self.assertEqual(youtube_id_from_url(url), "", url)


class VideoPagesTests(TestCase):
    def setUp(self):
        VideoRealisation.objects.all().delete()

    def test_lien_invalide_refuse_dans_le_formulaire(self):
        video = VideoRealisation(title="X", youtube_url="https://vimeo.com/123")
        with self.assertRaises(ValidationError):
            video.full_clean()

    def test_pages_affichent_seulement_les_videos_publiees(self):
        VideoRealisation.objects.create(title="Visible", youtube_url="https://youtu.be/aaaaaaaaaaa", order=1)
        VideoRealisation.objects.create(title="Pas accueil", youtube_url="https://youtu.be/bbbbbbbbbbb",
                                        show_on_home=False, order=2)
        VideoRealisation.objects.create(title="Brouillon", youtube_url="https://youtu.be/ccccccccccc",
                                        is_published=False, order=3)

        home = self.client.get(reverse("core:home")).content.decode()
        self.assertIn('data-yt-play="aaaaaaaaaaa"', home)
        self.assertNotIn("bbbbbbbbbbb", home)
        self.assertNotIn("ccccccccccc", home)

        page = self.client.get(reverse("core:realisations")).content.decode()
        self.assertIn("embed/aaaaaaaaaaa", page)
        self.assertIn("embed/bbbbbbbbbbb", page)
        self.assertNotIn("ccccccccccc", page)

    def test_accueil_limite_a_quatre_videos(self):
        for i in range(6):
            VideoRealisation.objects.create(title=f"V{i}", youtube_url=f"https://youtu.be/{'abcdef'[i] * 11}", order=i)
        home = self.client.get(reverse("core:home")).content.decode()
        self.assertEqual(home.count("data-yt-play="), 4)


class DashboardVideoTests(TestCase):
    def setUp(self):
        from .factories import make_staff, make_user

        VideoRealisation.objects.all().delete()
        self.staff = make_staff("equipe", role="ADMIN")
        self.client_user = make_user("visiteur")

    def test_reserve_a_l_equipe(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse("dashboard:videos_list"))
        self.assertNotEqual(response.status_code, 200)

    def test_ajout_et_bascule_depuis_le_dashboard(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse("dashboard:videos_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("dashboard:videos_create")).status_code, 200)

        response = self.client.post(reverse("dashboard:videos_create"), {
            "youtube_url": "https://youtu.be/mDGgGi5hjFI?si=abc", "title": "Nouvelle vidéo",
            "category": "live", "order": 5, "is_published": "on", "show_on_home": "on",
        })
        self.assertRedirects(response, reverse("dashboard:videos_list"))
        video = VideoRealisation.objects.get()
        self.assertEqual(video.youtube_id, "mDGgGi5hjFI")

        self.client.post(reverse("dashboard:videos_toggle", args=[video.pk]), {"field": "is_published"})
        video.refresh_from_db()
        self.assertFalse(video.is_published)

        self.assertEqual(self.client.get(reverse("dashboard:videos_edit", args=[video.pk])).status_code, 200)
        self.client.post(reverse("dashboard:videos_delete", args=[video.pk]))
        self.assertFalse(VideoRealisation.objects.exists())

    def test_lien_invalide_affiche_une_erreur(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard:videos_create"), {
            "youtube_url": "https://vimeo.com/123", "title": "X", "category": "live", "order": 1,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(VideoRealisation.objects.exists())
        self.assertContains(response, "Lien YouTube non reconnu")
