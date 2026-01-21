from django.db import models
# from django import forms
from django.conf import settings
from django.utils import timezone
# from django.core.exceptions import ValidationError
from .choices import (
    EquipmentStatus,
    ReservationStatus,
    StudioTypeChoices,
    StudioStatusChoices,
    ProjectFormatChoices,
    PreferredPeriodChoices,
    DeliveryDeadlineChoices,
)



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


# class Reservation(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
#     studio = models.ForeignKey(Studio, on_delete=models.SET_NULL, null=True, blank=True)
#     equipments = models.ManyToManyField(Equipment, blank=True, related_name='reservations')
#     service = models.ForeignKey(
#         'services_app.Service',  # model Service de l’app services_app
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='reservations',
#     )
#     start_datetime = models.DateTimeField("Début")
#     end_datetime = models.DateTimeField("Fin")
#     status = models.CharField(
#         "Statut",
#         max_length=20,
#         choices=ReservationStatus.choices,
#         default=ReservationStatus.PENDING,
#     )
#     admin_comment = models.TextField("Commentaire admin", blank=True)
#     created_at = models.DateTimeField("Créée le", auto_now_add=True)
#     assigned_technician = models.ForeignKey(
#         User,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='assigned_reservations',
#         verbose_name="Technicien assigné",
#     )

#     class Meta:
#         verbose_name = "Réservation"
#         verbose_name_plural = "Réservations"
#         ordering = ['-created_at']

#     def is_past(self):
#         return self.end_datetime < timezone.now()

#     def __str__(self):
#         return f"Réservation #{self.id} - {self.user} - {self.start_datetime:%d/%m/%Y}"


#============================================================== pour le nouveau reservation =======================================================
class Reservation(models.Model):
    # --- LIENS INTERNES / TECHNIQUES ---
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name="Utilisateur"
    )
    studio = models.ForeignKey(
        Studio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Studio"
    )
    equipments = models.ManyToManyField(
        Equipment,
        blank=True,
        related_name='reservations',
        verbose_name="Équipements"
    )
    service = models.ForeignKey(
        'services_app.Service',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservations',
        verbose_name="Service associé",
    )

    # 🧩 1. VOS INFORMATIONS (snapshot pour la demande)
    contact_full_name = models.CharField(
        "Nom & Prénom",
        max_length=150,
        blank=True,
        help_text="Nom de la personne à contacter pour ce projet."
    )
    contact_company = models.CharField(
        "Nom de la structure / marque",
        max_length=150,
        blank=True
    )
    contact_phone = models.CharField(
        "Téléphone",
        max_length=50,
        blank=True
    )
    contact_email = models.EmailField(
        "Email",
        blank=True
    )
    contact_city = models.CharField(
        "Ville",
        max_length=100,
        blank=True
    )
    contact_country = models.CharField(
        "Pays",
        max_length=100,
        blank=True
    )

    # 🎬 2. VOTRE PROJET VIDÉO
    project_summary = models.TextField(
        "Résumé du projet vidéo",
        blank=True,
        help_text="Objectif, cible, type de contenu…"
    )
    project_references = models.TextField(
        "Exemples / références qui vous inspirent",
        blank=True,
        help_text="Liens YouTube, Instagram, émissions, podcasts, etc."
    )

    # 🎙️ 3. FORMAT & CONFIGURATION DU PLATEAU
    format_type = models.CharField(
        "Type de format",
        max_length=20,
        choices=ProjectFormatChoices.choices,
        blank=True
    )
    participants_count = models.PositiveIntegerField(
        "Nombre total d'intervenants sur le plateau",
        blank=True,
        null=True
    )
    participants_details = models.CharField(
        "Détails sur les intervenants",
        max_length=255,
        blank=True,
        help_text="À préciser si plus de 4 intervenants ou configuration spéciale."
    )

    # ⏱️ 4. DURÉE & VOLUME DE PRODUCTION
    episode_duration_minutes = models.PositiveIntegerField(
        "Durée moyenne par épisode (en minutes)",
        blank=True,
        null=True,
        help_text="Exemples : 3, 7, 13, 26…"
    )
    episodes_count = models.PositiveIntegerField(
        "Nombre d'épisodes à tourner",
        blank=True,
        null=True
    )
    episodes_notes = models.CharField(
        "Précisions sur le nombre d'épisodes",
        max_length=255,
        blank=True,
        help_text="À utiliser si '2 à 5', '6 à 10' ou 'plus'."
    )

    # 📅 5. PÉRIODE D’ENREGISTREMENT SOUHAITÉE
    preferred_period = models.CharField(
        "Période préférée",
        max_length=20,
        choices=PreferredPeriodChoices.choices,
        blank=True
    )
    preferred_date_1 = models.DateTimeField(
        "1ère date souhaitée",
        blank=True,
        null=True
    )
    preferred_date_2 = models.DateTimeField(
        "2ᵉ date souhaitée",
        blank=True,
        null=True
    )
    scheduling_notes = models.TextField(
        "Notes sur la planification",
        blank=True,
        help_text="Contraintes d'horaires, plage horaire idéale, etc."
    )

    # 🎥 6. TYPE D’ACCOMPAGNEMENT SOUHAITÉ
    rental_studio_only = models.BooleanField(
        "Location du studio uniquement",
        default=False
    )
    option_custom_set = models.BooleanField(
        "Studio + décor personnalisé",
        default=False
    )
    option_make_up = models.BooleanField(
        "Studio + décor + maquilleuse professionnelle",
        default=False
    )
    option_technical_team = models.BooleanField(
        "Équipe technique (cadrage, son, lumière)",
        default=False
    )
    option_video_editing = models.BooleanField(
        "Besoin de montage vidéo",
        default=False
    )
    option_express_delivery = models.BooleanField(
        "Livraison express souhaitée",
        default=False
    )
    support_other_details = models.TextField(
        "Précisions complémentaires sur l'accompagnement",
        blank=True
    )

    # ⏳ 7. DÉLAIS & ATTENTES
    delivery_deadline = models.CharField(
        "Délai de livraison souhaité",
        max_length=20,
        choices=DeliveryDeadlineChoices.choices,
        blank=True
    )
    specific_constraints = models.TextField(
        "Contraintes particulières",
        blank=True,
        help_text="Lancement, événement, diffusion à date précise, etc."
    )

    # 💰 8. BUDGET INDICATIF
    budget_known = models.BooleanField(
        "Le client a une idée de son budget",
        default=False
    )
    budget_min = models.DecimalField(
        "Budget minimum (FCFA)",
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    budget_max = models.DecimalField(
        "Budget maximum (FCFA)",
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    budget_notes = models.TextField(
        "Commentaires sur le budget",
        blank=True,
        help_text="Par ex. 'Je souhaite être conseillé'."
    )

    # 🤝 9. BESOIN D’ÉCHANGER AVANT ?
    contact_pref_call = models.BooleanField(
        "Souhaite être rappelé par un conseiller technique",
        default=False
    )
    contact_pref_meeting = models.BooleanField(
        "Souhaite prendre rendez-vous pour en discuter",
        default=False
    )
    contact_pref_email_quote = models.BooleanField(
        "Préfère recevoir un devis détaillé par email",
        default=False
    )

    # --- SUIVI INTERNE / PLANNING CONFIRMÉ ---
    start_datetime = models.DateTimeField("Début")
    end_datetime = models.DateTimeField("Fin")
    status = models.CharField(
        "Statut",
        max_length=20,
        choices=ReservationStatus.choices,
        default=ReservationStatus.PENDING,
    )
    admin_comment = models.TextField("Commentaire admin", blank=True)
    client_additional_message = models.TextField(
        "Message complémentaire du client",
        blank=True
    )
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
 
    
# class ReservationStatusHistory(models.Model):
#     """
#     Historique des changements de statut d'une réservation.
#     """
#     reservation = models.ForeignKey(
#         Reservation,
#         on_delete=models.CASCADE,
#         related_name='status_history',
#         verbose_name="Réservation",
#     )
#     old_status = models.CharField(
#         "Ancien statut",
#         max_length=20,
#         choices=ReservationStatus.choices,
#     )
#     new_status = models.CharField(
#         "Nouveau statut",
#         max_length=20,
#         choices=ReservationStatus.choices,
#     )
#     changed_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='reservation_status_changes',
#         verbose_name="Modifié par",
#     )
#     changed_at = models.DateTimeField("Modifié le", auto_now_add=True)
#     note = models.TextField("Note / commentaire", blank=True)

#     class Meta:
#         verbose_name = "Historique de statut de réservation"
#         verbose_name_plural = "Historiques de statut de réservation"
#         ordering = ['-changed_at']

#     def __str__(self):
#         return f"Réservation #{self.reservation_id} : {self.old_status} -> {self.new_status}"


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