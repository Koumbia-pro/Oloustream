from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

User = get_user_model()


class Region(models.Model):
    """Régions/Villes du Burkina Faso"""
    name = models.CharField(max_length=100, unique=True)
    is_priority = models.BooleanField(
        default=False,
        help_text="Zone prioritaire (Bobo, Koudougou, etc.)"
    )
    active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Région"
        ordering = ['-is_priority', 'name']
    
    def __str__(self):
        return f"{self.name} (prioritaire)" if self.is_priority else self.name


class PartnerApplication(models.Model):
    """Candidature pour devenir partenaire d'affaires"""
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('reviewing', 'En cours d\'examen'),
        ('interview', 'Entretien planifié'),
        ('approved', 'Approuvée'),
        ('rejected', 'Rejetée'),
    ]
    
    NETWORK_STRENGTH = [
        ('weak', 'Limité'),
        ('medium', 'Moyen'),
        ('strong', 'Fort'),
        ('very_strong', 'Très fort'),
    ]
    
    # Informations personnelles
    full_name = models.CharField("Nom complet", max_length=200)
    phone = models.CharField("Téléphone", max_length=20)
    email = models.EmailField("Email", blank=True)
    whatsapp = models.CharField("WhatsApp", max_length=20, blank=True)
    
    # Documents
    id_type = models.CharField(
        "Type de pièce",
        max_length=20,
        choices=[('cnib', 'CNIB'), ('passport', 'Passeport')],
        default='cnib'
    )
    id_number = models.CharField("Numéro de pièce", max_length=50)
    id_document = models.FileField(
        "Copie de la pièce",
        upload_to='partners/documents/',
        blank=True
    )
    
    # Localisation
    city = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Ville/Région"
    )
    address = models.TextField("Adresse", blank=True)
    
    # Profil professionnel
    current_activity = models.CharField(
        "Activité actuelle",
        max_length=200,
        help_text="Ex: Entrepreneur, Commercial, Journaliste..."
    )
    experience_years = models.IntegerField(
        "Années d'expérience",
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        default=0
    )
    
    # Réseau et compétences
    network_strength = models.CharField(
        "Force du réseau",
        max_length=20,
        choices=NETWORK_STRENGTH,
        default='medium'
    )
    network_description = models.TextField(
        "Description du réseau",
        help_text="Institutions, entreprises, secteurs d'activité que vous connaissez"
    )
    
    sectors_knowledge = models.TextField(
        "Secteurs de compétence",
        help_text="Ex: Événementiel, ONG, Corporate, Médias..."
    )
    
    why_oloustream = models.TextField(
        "Pourquoi Oloustream ?",
        help_text="Motivations pour ce partenariat"
    )
    
    # Disponibilité
    availability = models.CharField(
        "Disponibilité",
        max_length=20,
        choices=[
            ('full_time', 'Temps plein'),
            ('part_time', 'Temps partiel'),
            ('flexible', 'Flexible'),
        ],
        default='flexible'
    )
    
    # Références (facultatif)
    references = models.TextField(
        "Références",
        blank=True,
        help_text="Noms et contacts de personnes pouvant attester de votre sérieux"
    )
    
    # Statut
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Notes internes (admin)
    internal_notes = models.TextField(
        "Notes internes",
        blank=True,
        help_text="Réservé à l'équipe Oloustream"
    )
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications'
    )
    
    class Meta:
        verbose_name = "Candidature partenaire"
        verbose_name_plural = "Candidatures partenaires"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} - {self.city} ({self.get_status_display()})"


class BusinessPartner(models.Model):
    """Partenaire d'affaires actif"""
    
    # Lien avec la candidature approuvée
    application = models.OneToOneField(
        PartnerApplication,
        on_delete=models.CASCADE,
        related_name='partner_profile'
    )
    
    # Utilisateur Django (créé après approbation)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='business_partner'
    )
    
    # Code partenaire unique
    partner_code = models.CharField(
        "Code partenaire",
        max_length=20,
        unique=True,
        help_text="Ex: BF-BOBO-001"
    )
    
    # Statut
    is_active = models.BooleanField("Actif", default=True)
    suspension_reason = models.TextField("Raison suspension", blank=True)
    
    # Commission (peut être personnalisée par partenaire)
    commission_rate = models.DecimalField(
        "Taux de commission (%)",
        max_digits=5,
        decimal_places=2,
        default=20.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Performance
    total_contracts = models.IntegerField("Contrats apportés", default=0)
    total_revenue = models.DecimalField(
        "CA généré (FCFA)",
        max_digits=15,
        decimal_places=2,
        default=0
    )
    total_commission_earned = models.DecimalField(
        "Commission totale (FCFA)",
        max_digits=12,
        decimal_places=2,
        default=0
    )
    total_commission_paid = models.DecimalField(
        "Commission versée (FCFA)",
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Dates
    activated_at = models.DateTimeField(auto_now_add=True)
    last_contract_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Partenaire d'affaires"
        verbose_name_plural = "Partenaires d'affaires"
        ordering = ['-total_revenue']
    
    def __str__(self):
        return f"{self.partner_code} - {self.user.get_full_name()}"
    
    @property
    def pending_commission(self):
        """Commission non encore versée"""
        return self.total_commission_earned - self.total_commission_paid


class Contract(models.Model):
    """Contrat apporté par un partenaire"""
    
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('pending', 'En attente de validation'),
        ('validated', 'Validé'),
        ('signed', 'Signé'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
    ]
    
    # Partenaire
    partner = models.ForeignKey(
        BusinessPartner,
        on_delete=models.PROTECT,
        related_name='contracts'
    )
    
    # Client
    client_name = models.CharField("Nom du client", max_length=200)
    client_type = models.CharField(
        "Type de client",
        max_length=50,
        choices=[
            ('institution', 'Institution'),
            ('ong', 'ONG'),
            ('company', 'Entreprise'),
            ('individual', 'Particulier'),
            ('event', 'Organisateur événement'),
        ]
    )
    client_contact = models.CharField("Contact client", max_length=200)
    
    # Détails du contrat
    service_type = models.CharField(
        "Type de service",
        max_length=100,
        help_text="Ex: Live streaming, Production vidéo, Formation..."
    )
    description = models.TextField("Description du projet")
    
    # Financier
    contract_amount = models.DecimalField(
        "Montant du contrat (FCFA)",
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    commission_rate = models.DecimalField(
        "Taux de commission appliqué (%)",
        max_digits=5,
        decimal_places=2
    )
    commission_amount = models.DecimalField(
        "Montant de la commission (FCFA)",
        max_digits=12,
        decimal_places=2,
        editable=False
    )
    
    # Documents
    contract_file = models.FileField(
        "Contrat signé",
        upload_to='partners/contracts/',
        blank=True
    )
    
    # Statut
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Validation
    validated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validated_contracts'
    )
    
    class Meta:
        verbose_name = "Contrat"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.client_name} - {self.contract_amount} FCFA"
    
    def save(self, *args, **kwargs):
        # Calcul automatique de la commission
        self.commission_amount = (
            self.contract_amount * self.commission_rate / 100
        )
        super().save(*args, **kwargs)


class CommissionPayment(models.Model):
    """Paiement de commission à un partenaire"""
    
    PAYMENT_METHODS = [
        ('orange_money', 'Orange Money'),
        ('bank_transfer', 'Virement bancaire'),
        ('check', 'Chèque'),
        ('cash', 'Espèces'),
    ]
    
    partner = models.ForeignKey(
        BusinessPartner,
        on_delete=models.PROTECT,
        related_name='payments'
    )
    
    # Contrats concernés
    contracts = models.ManyToManyField(
        Contract,
        related_name='commission_payments',
        help_text="Contrats pour lesquels cette commission est versée"
    )
    
    amount = models.DecimalField(
        "Montant versé (FCFA)",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    payment_method = models.CharField(
        "Méthode de paiement",
        max_length=20,
        choices=PAYMENT_METHODS
    )
    
    reference = models.CharField(
        "Référence de paiement",
        max_length=100,
        blank=True
    )
    
    receipt = models.FileField(
        "Reçu/Preuve",
        upload_to='partners/payments/',
        blank=True
    )
    
    notes = models.TextField("Notes", blank=True)
    
    paid_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    
    class Meta:
        verbose_name = "Paiement de commission"
        verbose_name_plural = "Paiements de commissions"
        ordering = ['-paid_at']
    
    def __str__(self):
        return f"{self.partner.partner_code} - {self.amount} FCFA ({self.paid_at.date()})"
