from urllib.parse import unquote

from django.test import TestCase
from django.urls import reverse

from .factories import make_studio


class WhatsappMessageTests(TestCase):
    def whatsapp_text(self, url):
        html = self.client.get(url).content.decode()
        start = html.index("https://wa.me/22664093196?text=") + len("https://wa.me/22664093196?text=")
        return unquote(html[start:html.index('"', start)])

    def test_message_par_defaut_sur_l_accueil(self):
        text = self.whatsapp_text(reverse("core:home"))
        self.assertIn("Je viens de votre site et je souhaite des informations sur vos services.", text)

    def test_message_adapte_aux_realisations(self):
        self.assertIn("J'ai adoré vos réalisations", self.whatsapp_text(reverse("core:realisations")))

    def test_message_avec_le_nom_du_studio(self):
        studio = make_studio("Studio Podcast")
        text = self.whatsapp_text(reverse("studio:user_studio_detail", args=[studio.pk]))
        self.assertIn("Le Studio Podcast a retenu mon attention", text)
