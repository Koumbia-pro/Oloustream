from django.db import models


class ContactRequest(models.Model):
    """Demande de contact ou de devis envoyée depuis le site public."""

    class Subject(models.TextChoices):
        QUOTE = "QUOTE", "Demande de devis"
        STUDIO = "STUDIO", "Location de studio"
        LIVE = "LIVE", "Live streaming / captation"
        EQUIPMENT = "EQUIPMENT", "Location de matériel"
        TRAINING = "TRAINING", "Formation"
        PARTNERSHIP = "PARTNERSHIP", "Partenariat"
        OTHER = "OTHER", "Autre demande"

    class Status(models.TextChoices):
        NEW = "NEW", "Nouvelle"
        IN_PROGRESS = "IN_PROGRESS", "En cours de traitement"
        DONE = "DONE", "Traitée"

    full_name = models.CharField("Nom complet", max_length=150)
    company = models.CharField("Structure / entreprise", max_length=150, blank=True)
    email = models.EmailField("Email")
    phone = models.CharField("Téléphone", max_length=40, blank=True)
    subject = models.CharField("Objet", max_length=20, choices=Subject.choices, default=Subject.QUOTE)
    event_date = models.DateField("Date souhaitée", null=True, blank=True)
    budget = models.CharField("Budget indicatif", max_length=100, blank=True)
    message = models.TextField("Message")

    status = models.CharField("Statut", max_length=20, choices=Status.choices, default=Status.NEW)
    internal_notes = models.TextField("Notes internes", blank=True)
    ip_address = models.GenericIPAddressField("Adresse IP", null=True, blank=True)
    created_at = models.DateTimeField("Reçue le", auto_now_add=True)

    class Meta:
        verbose_name = "Demande de contact"
        verbose_name_plural = "Demandes de contact"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} — {self.get_subject_display()} ({self.created_at:%d/%m/%Y})"


class VideoRealisation(models.Model):
    """Vidéo YouTube affichée dans les réalisations (accueil et page Réalisations)."""

    class Category(models.TextChoices):
        LIVE = "live", "Live & événements"
        PRODUCTION = "production", "Production vidéo"
        DIGITAL = "digital", "Digital"

    title = models.CharField("Titre", max_length=200)
    youtube_url = models.CharField(
        "Lien YouTube",
        max_length=300,
        help_text="Collez le lien de la vidéo (youtu.be/…, youtube.com/watch?v=…, Shorts…).",
    )
    youtube_id = models.CharField("Identifiant YouTube", max_length=20, editable=False)
    category = models.CharField("Catégorie (filtre)", max_length=20, choices=Category.choices,
                                default=Category.PRODUCTION)
    subtitle = models.CharField("Sous-titre court", max_length=80, blank=True,
                                help_text="Affiché sous la vidéo sur l'accueil. Ex. : Portrait · Entrepreneuriat")
    description = models.TextField("Description", blank=True,
                                   help_text="Affichée sur la page Réalisations (1 ou 2 phrases).")
    tags = models.CharField("Étiquettes", max_length=120, blank=True,
                            help_text="Séparées par des virgules. Ex. : Portrait, Production")
    show_on_home = models.BooleanField("Afficher sur l'accueil", default=True,
                                       help_text="Les 4 premières vidéos cochées apparaissent sur l'accueil.")
    is_published = models.BooleanField("Publiée", default=True)
    order = models.PositiveIntegerField("Ordre", default=0, help_text="Les plus petits numéros s'affichent en premier.")
    created_at = models.DateTimeField("Ajoutée le", auto_now_add=True)

    class Meta:
        verbose_name = "Vidéo de réalisation"
        verbose_name_plural = "Vidéos de réalisations"
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.title

    def clean(self):
        from django.core.exceptions import ValidationError
        from .utils import youtube_id_from_url

        if not youtube_id_from_url(self.youtube_url):
            raise ValidationError({"youtube_url": "Lien YouTube non reconnu. Copiez le lien depuis le bouton « Partager » de YouTube."})

    def save(self, *args, **kwargs):
        from .utils import youtube_id_from_url

        self.youtube_id = youtube_id_from_url(self.youtube_url) or self.youtube_id
        super().save(*args, **kwargs)

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    @property
    def thumbnail_url(self):
        return f"https://i.ytimg.com/vi/{self.youtube_id}/hqdefault.jpg"

    @property
    def watch_url(self):
        return f"https://www.youtube.com/watch?v={self.youtube_id}"


class Testimonial(models.Model):
    """Témoignage client affiché sur l'accueil (section « Ils nous font confiance »)."""

    quote = models.TextField("Témoignage", help_text="Les mots du client, sans guillemets (ils sont ajoutés automatiquement).")
    author_name = models.CharField("Nom de la personne", max_length=120, blank=True,
                                   help_text="Laissez vide si le client préfère rester anonyme.")
    author_role = models.CharField("Fonction", max_length=120, help_text="Ex. : Responsable communication")
    organization = models.CharField("Structure / entreprise", max_length=150, blank=True,
                                    help_text="Ex. : UNICEF Burkina Faso")
    photo = models.ImageField("Photo ou logo", upload_to="testimonials/", blank=True, null=True)
    is_published = models.BooleanField("Publié", default=True)
    order = models.PositiveIntegerField("Ordre", default=0, help_text="Les plus petits numéros s'affichent en premier.")
    created_at = models.DateTimeField("Ajouté le", auto_now_add=True)

    class Meta:
        verbose_name = "Témoignage client"
        verbose_name_plural = "Témoignages clients"
        ordering = ["order", "-created_at"]

    def __str__(self):
        who = self.author_name or self.author_role
        return f"{who} — {self.organization}" if self.organization else who

    @property
    def initials(self):
        source = self.author_name or self.organization or self.author_role
        words = ["".join(ch for ch in word if ch.isalpha()) for word in source.split()]
        return "".join(word[0] for word in words if word)[:2].upper()
