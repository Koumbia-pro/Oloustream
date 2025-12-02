from django.db import models
# from django import forms
from django.conf import settings
from django.utils import timezone
# from django.core.exceptions import ValidationError
from .choices import EquipmentStatus, ReservationStatus, StudioTypeChoices, StudioStatusChoices



User = settings.AUTH_USER_MODEL


class Studio(models.Model):
    # INFOS DE BASE
    name = models.CharField("Nom du studio", max_length=150)
    code = models.CharField(
        "Code du studio",
        max_length=50,
        blank=True,
        help_text="Code interne (optionnel), utile pour l'administration."
    )
    description = models.TextField("Description détaillée", blank=True)

    studio_type = models.CharField(
        "Type de studio",
        max_length=20,
        choices=StudioTypeChoices.choices,
        default=StudioTypeChoices.MULTI,
    )

    # LOCALISATION
    address = models.CharField("Adresse complète", max_length=255, blank=True)
    city = models.CharField("Ville", max_length=100, blank=True)
    country = models.CharField("Pays", max_length=100, blank=True)

     # IMAGE PRINCIPALE
    image = models.ImageField(
        "Image principale du studio",
        upload_to="studios/",
        blank=True,
        null=True,
    )

    # DIMENSIONS
    length_m = models.DecimalField(
        "Longueur (m)",
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
    )
    width_m = models.DecimalField(
        "Largeur (m)",
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
    )
    height_m = models.DecimalField(
        "Hauteur (m)",
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
    )
    area_m2 = models.DecimalField(
        "Superficie (m²)",
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Si laissé vide, sera calculé automatiquement (longueur x largeur)."
    )

    # ÉCLAIRAGE
    lighting_included = models.BooleanField(
        "Éclairage intégré",
        default=False,
        help_text="Cochez si le studio est équipé d'un éclairage intégré."
    )
    lighting_type = models.TextField(
        "Type de lumières (LED, projecteurs, softbox…)",
        blank=True,
    )

    # ÉQUIPEMENTS INCLUS
    equip_cameras = models.TextField("Caméras présentes", blank=True)
    equip_microphones = models.TextField("Micros disponibles", blank=True)
    equip_lights = models.TextField("Lumières", blank=True)
    equip_screens = models.TextField("Écrans", blank=True)
    equip_control_room = models.TextField("Régie", blank=True)
    equip_accessories = models.TextField("Accessoires", blank=True)

    # TARIFICATION
    price_per_hour = models.DecimalField(
        "Prix par heure (FCFA)",
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    price_half_day = models.DecimalField(
        "Prix par demi-journée (FCFA)",
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    price_day = models.DecimalField(
        "Prix par journée (FCFA)",
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    extra_options = models.TextField(
        "Options supplémentaires (liste)",
        blank=True,
        help_text="Exemple : Fondu décor, enregistrement multi‑cam, etc."
    )
    discount_percent = models.PositiveIntegerField(
        "Réduction / promotion (%)",
        blank=True,
        null=True,
    )

    # DISPONIBILITÉS
    opening_hours = models.CharField(
        "Heures d'ouverture",
        max_length=100,
        blank=True,
        help_text="Exemple : 08h00 - 20h00"
    )
    opening_days = models.CharField(
        "Jours d'ouverture",
        max_length=100,
        blank=True,
        help_text="Exemple : Lundi au samedi"
    )
    unavailable_dates = models.TextField(
        "Dates indisponibles",
        blank=True,
        help_text="Exemple : 25/12, 01/01, etc. (ou note libre)"
    )

    # CAPACITÉ
    capacity = models.PositiveIntegerField(
        "Capacité maximale (nombre de personnes)",
        blank=True,
        null=True,
    )
    technicians_required = models.PositiveIntegerField(
        "Nombre de techniciens requis",
        blank=True,
        null=True,
    )

    # STATUT GLOBAL
    status = models.CharField(
        "Statut du studio",
        max_length=20,
        choices=StudioStatusChoices.choices,
        default=StudioStatusChoices.AVAILABLE,
    )
    is_active = models.BooleanField(
        "Actif",
        default=True,
        help_text="Si décoché, le studio sera masqué côté utilisateur."
    )

    class Meta:
        verbose_name = "Studio"
        verbose_name_plural = "Studios"
        ordering = ["name"]

    def __str__(self):
        if self.code:
            return f"{self.name} ({self.code})"
        return self.name

    def save(self, *args, **kwargs):
        # Calcul automatique de la superficie si longueur & largeur définies
        if self.length_m and self.width_m and not self.area_m2:
            self.area_m2 = self.length_m * self.width_m
        super().save(*args, **kwargs)


class EquipmentCategory(models.Model):
    name = models.CharField("Nom de la catégorie", max_length=100)
    description = models.TextField("Description", blank=True)

    class Meta:
        verbose_name = "Catégorie d'équipement"
        verbose_name_plural = "Catégories d'équipements"

    def __str__(self):
        return self.name


class Equipment(models.Model):
    # INFORMATIONS DE BASE
    name = models.CharField("Nom de l'équipement", max_length=150)
    brand = models.CharField("Marque", max_length=100, blank=True)
    model = models.CharField("Modèle", max_length=100, blank=True)
    category = models.ForeignKey(
        EquipmentCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipments',
        verbose_name="Catégorie",
    )
    serial_number = models.CharField(
        "Numéro de série",
        max_length=100,
        unique=True,
        blank=True,
        null=True,
    )

    # INFORMATIONS D'ACHAT
    purchase_date = models.DateField("Date d'achat", blank=True, null=True)
    purchase_price = models.DecimalField(
        "Prix d'achat",
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )

    # ÉTAT & DISPONIBILITÉ
    status = models.CharField(
        "Statut",
        max_length=20,
        choices=EquipmentStatus.choices,
        default=EquipmentStatus.AVAILABLE,
    )
    is_available_for_rent = models.BooleanField("Disponible à la location", default=True)
    current_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_equipments',
        verbose_name="Utilisateur actuel",
    )
    location = models.CharField("Emplacement physique", max_length=150, blank=True)

    # SPÉCIFICATIONS TECHNIQUES
    technical_specs = models.TextField(
        "Spécifications techniques (poids, dimensions, puissance, etc.)",
        blank=True,
    )
    accessories_included = models.TextField(
        "Accessoires inclus (câbles, batteries, etc.)",
        blank=True,
    )
    important_notes = models.TextField(
        "Notes importantes",
        blank=True,
    )

    # MAINTENANCE
    last_maintenance_date = models.DateField("Dernière maintenance", blank=True, null=True)
    next_maintenance_date = models.DateField("Prochaine maintenance", blank=True, null=True)
    maintenance_notes = models.TextField(
        "Notes de maintenance (réparations, problèmes)",
        blank=True,
    )

    # DOCUMENTS & IMAGES
    photo = models.ImageField(
        "Photo de l'équipement",
        upload_to='equipment_photos/',
        blank=True,
        null=True,
    )
    manual = models.FileField(
        "Manuel d'utilisation (PDF)",
        upload_to='equipment_manuals/',
        blank=True,
        null=True,
    )

    # MÉTADONNÉES
    created_at = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Équipement"
        verbose_name_plural = "Équipements"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.brand or ''} {self.model or ''})".strip()

    @property
    def age_years(self):
        """
        Âge de l'équipement (en années, approximatif).
        """
        if not self.purchase_date:
            return None
        # On utilise la date locale Django
        today = timezone.localdate()
        delta_years = today.year - self.purchase_date.year
        # Ajustement si l'anniversaire n'est pas encore passé cette année
        if (today.month, today.day) < (self.purchase_date.month, self.purchase_date.day):
            delta_years -= 1
        return max(delta_years, 0)

    @property
    def maintenance_alert(self):
        """
        True si une maintenance est nécessaire (date prochaine <= aujourd'hui).
        """
        if not self.next_maintenance_date:
            return False
        # On utilise aussi timezone.localdate()
        today = timezone.localdate()
        return self.next_maintenance_date <= today


class EquipmentUsageHistory(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='usage_history')
    start_datetime = models.DateTimeField("Début d'utilisation")
    end_datetime = models.DateTimeField("Fin d'utilisation", blank=True, null=True)
    used_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField("Notes", blank=True)

    class Meta:
        verbose_name = "Historique d'utilisation"
        verbose_name_plural = "Historiques d'utilisation"

    def __str__(self):
        return f"{self.equipment} - {self.start_datetime}"


class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    studio = models.ForeignKey(Studio, on_delete=models.SET_NULL, null=True, blank=True)
    equipments = models.ManyToManyField(Equipment, blank=True, related_name='reservations')
    service = models.ForeignKey(
        'services_app.Service',  # model Service de l’app services_app
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservations',
    )
    start_datetime = models.DateTimeField("Début")
    end_datetime = models.DateTimeField("Fin")
    status = models.CharField(
        "Statut",
        max_length=20,
        choices=ReservationStatus.choices,
        default=ReservationStatus.PENDING,
    )
    admin_comment = models.TextField("Commentaire admin", blank=True)
    created_at = models.DateTimeField("Créée le", auto_now_add=True)
    assigned_technician = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_reservations',
        verbose_name="Technicien assigné",
    )

    class Meta:
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
        ordering = ['-created_at']

    def is_past(self):
        return self.end_datetime < timezone.now()

    def __str__(self):
        return f"Réservation #{self.id} - {self.user} - {self.start_datetime:%d/%m/%Y}"
 
    
class ReservationStatusHistory(models.Model):
    """
    Historique des changements de statut d'une réservation.
    """
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name="Réservation",
    )
    old_status = models.CharField(
        "Ancien statut",
        max_length=20,
        choices=ReservationStatus.choices,
    )
    new_status = models.CharField(
        "Nouveau statut",
        max_length=20,
        choices=ReservationStatus.choices,
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservation_status_changes',
        verbose_name="Modifié par",
    )
    changed_at = models.DateTimeField("Modifié le", auto_now_add=True)
    note = models.TextField("Note / commentaire", blank=True)

    class Meta:
        verbose_name = "Historique de statut de réservation"
        verbose_name_plural = "Historiques de statut de réservation"
        ordering = ['-changed_at']

    def __str__(self):
        return f"Réservation #{self.reservation_id} : {self.old_status} -> {self.new_status}"
    

# class EquipmentReservationForm(forms.ModelForm):
#     """
#     Formulaire simplifié pour réserver un matériel précis (depuis la page de l'équipement).
#     L'équipement sera ajouté dans la vue, pas par l'utilisateur.
#     """
#     class Meta:
#         model = Reservation
#         fields = ("start_datetime", "end_datetime")
#         widgets = {
#             "start_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
#             "end_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
#         }

#     def clean(self):
#         cleaned_data = super().clean()
#         start = cleaned_data.get("start_datetime")
#         end = cleaned_data.get("end_datetime")

#         if start and end:
#             if start >= end:
#                 raise ValidationError("La date/heure de début doit être avant la date/heure de fin.")
#             if start < timezone.now():
#                 raise ValidationError("La date/heure de début doit être dans le futur.")

#         return cleaned_data