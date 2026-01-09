from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class ServiceTypeChoices(models.TextChoices):
    LIVE_STREAMING = 'LIVE_STREAMING', 'Live streaming'
    PRODUCTION = 'PRODUCTION', 'Production audiovisuelle'
    POST_PROD = 'POST_PROD', 'Post-production'
    RENTAL = 'RENTAL', 'Location matériel'
    TRAINING = 'TRAINING', 'Formation'
    CONSULTING = 'CONSULTING', 'Conseil'
    OTHER = 'OTHER', 'Autre'


class LocationTypeChoices(models.TextChoices):
    ONSITE = 'ONSITE', 'Sur site (client)'
    STUDIO = 'STUDIO', 'En studio'
    REMOTE = 'REMOTE', 'À distance'
    HYBRID = 'HYBRID', 'Hybride' 


class DifficultyLevelChoices(models.TextChoices):
    BASIC = 'BASIC', 'Basique'
    STANDARD = 'STANDARD', 'Standard'
    PREMIUM = 'PREMIUM', 'Premium'
    CUSTOM = 'CUSTOM', 'Sur-mesure'


class TrainingLevelChoices(models.TextChoices):
    BEGINNER = 'BEGINNER', 'Débutant'
    INTERMEDIATE = 'INTERMEDIATE', 'Intermédiaire'
    ADVANCED = 'ADVANCED', 'Avancé'
    ALL_LEVELS = 'ALL_LEVELS', 'Tous niveaux'


class TrainingModeChoices(models.TextChoices):
    ONSITE = 'ONSITE', 'Présentiel'
    ONLINE = 'ONLINE', 'En ligne'
    HYBRID = 'HYBRID', 'Hybride'


class PartnershipTypeChoices(models.TextChoices):
    CLIENT = 'CLIENT', 'Client'
    SUPPLIER = 'SUPPLIER', 'Fournisseur'
    SPONSOR = 'SPONSOR', 'Sponsor'
    MEDIA = 'MEDIA', 'Partenaire média'
    OTHER = 'OTHER', 'Autre'



class TrainingCategory(models.Model):
    name = models.CharField("Nom de la catégorie de formation", max_length=150)
    description = models.TextField("Description", blank=True)
    icon = models.CharField("Icône (classe CSS)", max_length=100, blank=True)

    class Meta:
        verbose_name = "Catégorie de formation"
        verbose_name_plural = "Catégories de formation"
        ordering = ['name']

    def __str__(self):
        return self.name


class Partner(models.Model):
    name = models.CharField("Nom du partenaire", max_length=150)
    logo = models.ImageField(upload_to='partners/', blank=True, null=True)
    website = models.URLField("Site web", blank=True)

    # Coordonnées de contact
    contact_name = models.CharField("Contact principal", max_length=150, blank=True)
    contact_email = models.EmailField("Email de contact", blank=True)
    contact_phone = models.CharField("Téléphone de contact", max_length=50, blank=True)

    # Type de partenariat
    partnership_type = models.CharField(
        "Type de partenariat",
        max_length=20,
        choices=PartnershipTypeChoices.choices,
        default=PartnershipTypeChoices.OTHER,
    )

    # Adresse & notes
    address = models.CharField("Adresse", max_length=255, blank=True)
    notes = models.TextField("Notes internes", blank=True)

    active = models.BooleanField("Actif", default=True)

    class Meta:
        verbose_name = "Partenaire"
        verbose_name_plural = "Partenaires"
        ordering = ['name']

    def __str__(self):
        return self.name

class ServiceCategory(models.Model):
    name = models.CharField("Nom de la catégorie", max_length=150)
    description = models.TextField("Description", blank=True)
    icon = models.CharField("Icône (classe CSS Phosphor ou autre)", max_length=100, blank=True)

    class Meta:
        verbose_name = "Catégorie de service"
        verbose_name_plural = "Catégories de services"
        ordering = ['name']

    def __str__(self):
        return self.name

class Service(models.Model):
    # INFOS DE BASE
    name = models.CharField("Nom du service", max_length=150)
    slug = models.SlugField(unique=True)
    short_description = models.CharField("Description courte", max_length=255, blank=True)
    description = models.TextField("Description détaillée")

    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='services',
        verbose_name="Catégorie",
    )
    service_type = models.CharField(
        "Type de service",
        max_length=20,
        choices=ServiceTypeChoices.choices,
        default=ServiceTypeChoices.OTHER,
    )

    # TARIFICATION & DURÉE
    base_price = models.DecimalField("Prix de base (F CFA)", max_digits=10, decimal_places=2)
    duration_min_minutes = models.PositiveIntegerField(
        "Durée minimale (minutes)",
        blank=True,
        null=True,
    )
    duration_max_minutes = models.PositiveIntegerField(
        "Durée maximale (minutes)",
        blank=True,
        null=True,
    )

    # LOGISTIQUE & COMPLEXITÉ
    location_type = models.CharField(
        "Lieu de prestation",
        max_length=20,
        choices=LocationTypeChoices.choices,
        default=LocationTypeChoices.STUDIO,
    )
    difficulty_level = models.CharField(
        "Niveau de complexité",
        max_length=20,
        choices=DifficultyLevelChoices.choices,
        default=DifficultyLevelChoices.STANDARD,
    )
    requires_studio = models.BooleanField("Nécessite un studio", default=False)
    requires_equipment_rental = models.BooleanField("Nécessite de la location matériel", default=False)

    # MÉDIA & STATUT
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    is_active = models.BooleanField("Actif", default=True)

    # NOTES INTERNES
    internal_notes = models.TextField("Notes internes (non visibles pour le client)", blank=True)

    # MÉTADONNÉES
    created_at = models.DateTimeField("Créé le", auto_now_add=True)
    updated_at = models.DateTimeField("Mis à jour le", auto_now=True)

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['name']

    def __str__(self):
        return self.name


class Offer(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='offers')
    title = models.CharField("Titre de l'offre", max_length=150)
    description = models.TextField("Description", blank=True)
    discount_percent = models.PositiveIntegerField("Réduction (%)", default=0)
    start_date = models.DateField("Date de début")
    end_date = models.DateField("Date de fin")
    is_active = models.BooleanField("Active", default=True)

    class Meta:
        verbose_name = "Offre"
        verbose_name_plural = "Offres"

    def __str__(self):
        return f"{self.title} ({self.service.name})"


class Training(models.Model):
    # INFOS DE BASE
    title = models.CharField("Titre de la formation", max_length=200)
    slug = models.SlugField(unique=True)
    short_description = models.CharField("Description courte", max_length=255, blank=True)
    description = models.TextField("Description détaillée")

    category = models.ForeignKey(
        TrainingCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trainings',
        verbose_name="Catégorie",
    )
    level = models.CharField(
        "Niveau",
        max_length=20,
        choices=TrainingLevelChoices.choices,
        default=TrainingLevelChoices.ALL_LEVELS,
    )
    mode = models.CharField(
        "Mode",
        max_length=20,
        choices=TrainingModeChoices.choices,
        default=TrainingModeChoices.ONSITE,
    )
    location = models.CharField("Lieu (si présentiel)", max_length=255, blank=True)

    # PÉDAGOGIE
    objectives = models.TextField("Objectifs pédagogiques", blank=True)
    prerequisites = models.TextField("Prérequis", blank=True)
    target_audience = models.TextField("Public cible", blank=True)
    program = models.TextField("Programme détaillé / modules", blank=True)

    # LOGISTIQUE & TARIFICATION
    duration_hours = models.PositiveIntegerField("Durée totale (heures)", blank=True, null=True)
    price = models.DecimalField("Prix (F CFA)", max_digits=10, decimal_places=2, blank=True, null=True)
    certification = models.BooleanField("Certification délivrée", default=False)
    max_seats = models.PositiveIntegerField("Nombre maximum de participants", blank=True, null=True)

    # CALENDRIER
    start_date = models.DateField("Date de début", blank=True, null=True)
    end_date = models.DateField("Date de fin", blank=True, null=True)
    schedule = models.TextField("Horaires / planning (ex : week-ends, soirs)", blank=True)

    # MÉDIA & STATUT
    image = models.ImageField("Image / visuel", upload_to='trainings/', blank=True, null=True)
    brochure = models.FileField("Brochure PDF", upload_to='training_brochures/', blank=True, null=True)
    is_active = models.BooleanField("Active", default=True)

    # MÉTADONNÉES
    created_at = models.DateTimeField("Créée le", auto_now_add=True)
    updated_at = models.DateTimeField("Mise à jour le", auto_now=True)

    class Meta:
        verbose_name = "Formation"
        verbose_name_plural = "Formations"
        ordering = ['title']

    def __str__(self):
        return self.title

class TrainingEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='training_enrollments')
    training = models.ForeignKey(Training, on_delete=models.CASCADE, related_name='enrollments')
    created_at = models.DateTimeField("Date d'inscription", auto_now_add=True)
    status = models.CharField("Statut", max_length=50, default='PENDING')  # PENDING, ACCEPTED, REJECTED

    class Meta:
        verbose_name = "Inscription à une formation"
        verbose_name_plural = "Inscriptions aux formations"
        unique_together = ('user', 'training')

    def __str__(self):
        return f"{self.user} -> {self.training} ({self.status})"
    

class OfferApplication(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='offer_applications',
        verbose_name="Utilisateur",
    )
    offer = models.ForeignKey(
        'Offer',
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name="Offre",
    )
    message = models.TextField("Message", blank=True)
    status = models.CharField("Statut", max_length=50, default='PENDING')  # PENDING, ACCEPTED, REJECTED
    created_at = models.DateTimeField("Date de candidature", auto_now_add=True)

    class Meta:
        verbose_name = "Candidature à une offre"
        verbose_name_plural = "Candidatures aux offres"
        unique_together = ('user', 'offer')

    def __str__(self):
        return f"{self.user} -> {self.offer} ({self.status})"
    


from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify

User = settings.AUTH_USER_MODEL


class JobOfferTypeChoices(models.TextChoices):
    INTERNSHIP = "INTERNSHIP", "Stage"
    JOB = "JOB", "Emploi"


class JobOfferStatusChoices(models.TextChoices):
    DRAFT = "DRAFT", "Brouillon"
    PUBLISHED = "PUBLISHED", "Publié"
    CLOSED = "CLOSED", "Fermé"


class ContractTypeChoices(models.TextChoices):
    CDI = "CDI", "CDI"
    CDD = "CDD", "CDD"
    FREELANCE = "FREELANCE", "Freelance"
    STAGE = "STAGE", "Stage"


class EducationLevelChoices(models.TextChoices):
    BAC = "BAC", "BAC"
    BAC_1 = "BAC+1", "BAC+1"
    BAC_2 = "BAC+2", "BAC+2"
    BAC_3 = "BAC+3", "BAC+3"
    BAC_4 = "BAC+4", "BAC+4"
    BAC_5 = "BAC+5", "BAC+5"


class JobOffer(models.Model):
    status = models.CharField(
        "Statut",
        max_length=20,
        choices=JobOfferStatusChoices.choices,
        default=JobOfferStatusChoices.DRAFT,
    )
    offer_type = models.CharField(
        "Type d'offre",
        max_length=20,
        choices=JobOfferTypeChoices.choices,
        default=JobOfferTypeChoices.JOB,
    )

    title = models.CharField("Titre", max_length=200)
    slug = models.SlugField(unique=True, blank=True)

    department = models.CharField("Département / Pôle", max_length=120, blank=True)
    location = models.CharField("Lieu", max_length=120, blank=True)

    contract_type = models.CharField(
        "Type de contrat",
        max_length=20,
        choices=ContractTypeChoices.choices,
        blank=True,
        default="",
    )
    level = models.CharField(
        "Niveau minimum",
        max_length=20,
        choices=EducationLevelChoices.choices,
        blank=True,
        default="",
    )

    summary = models.CharField("Résumé", max_length=255, blank=True)
    description = models.TextField("Description complète")

    responsibilities = models.TextField("Missions", blank=True)
    requirements = models.TextField("Profil recherché", blank=True)
    benefits = models.TextField("Avantages", blank=True)

    deadline = models.DateField("Date limite", blank=True, null=True)

    poster = models.ImageField("Affiche / visuel", upload_to="job_offers/posters/", blank=True, null=True)

    created_at = models.DateTimeField("Créé le", auto_now_add=True)
    updated_at = models.DateTimeField("Mis à jour le", auto_now=True)

    class Meta:
        verbose_name = "Offre (Recrutement)"
        verbose_name_plural = "Offres (Recrutement)"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_offer_type_display()} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:50] or "offre"
            slug = base
            i = 2
            while JobOffer.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def is_open(self) -> bool:
        if self.status != JobOfferStatusChoices.PUBLISHED:
            return False
        if self.deadline and self.deadline < timezone.localdate():
            return False
        return True


class JobApplicationStatusChoices(models.TextChoices):
    PENDING = "PENDING", "En attente"
    ACCEPTED = "ACCEPTED", "Accepté"
    REJECTED = "REJECTED", "Refusé"


class JobApplication(models.Model):
    offer = models.ForeignKey(
        JobOffer,
        on_delete=models.CASCADE,
        related_name="applications",
        verbose_name="Offre",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="job_applications",
        verbose_name="Utilisateur",
    )

    full_name = models.CharField("Nom complet", max_length=150)
    email = models.EmailField("Email")
    phone = models.CharField("Téléphone", max_length=50, blank=True)

    cv = models.FileField("CV (PDF)", upload_to="job_applications/cv/")
    cover_letter = models.TextField("Message / lettre", blank=True)
    portfolio_url = models.URLField("Portfolio / LinkedIn", blank=True)

    status = models.CharField(
        "Statut",
        max_length=20,
        choices=JobApplicationStatusChoices.choices,
        default=JobApplicationStatusChoices.PENDING,
    )
    internal_note = models.TextField("Note interne", blank=True)

    created_at = models.DateTimeField("Candidature le", auto_now_add=True)

    class Meta:
        verbose_name = "Candidature (Recrutement)"
        verbose_name_plural = "Candidatures (Recrutement)"
        ordering = ["-created_at"]
        unique_together = ("offer", "user")

    def __str__(self):
        return f"{self.full_name} -> {self.offer.title}"