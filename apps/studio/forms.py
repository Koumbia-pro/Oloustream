# apps/studio/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Equipment, Reservation, Studio


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = (
            # Infos de base
            "name",
            "brand",
            "model",
            "category",
            "serial_number",
            # Achat
            "purchase_date",
            "purchase_price",
            # État & dispo
            "status",
            "is_available_for_rent",
            "current_user",
            "location",
            # Spécifications
            "technical_specs",
            "accessories_included",
            "important_notes",
            # Maintenance
            "last_maintenance_date",
            "next_maintenance_date",
            "maintenance_notes",
            # Documents
            "photo",
            "manual",
        )
        widgets = {
            "purchase_date": forms.DateInput(attrs={"type": "date"}),
            "last_maintenance_date": forms.DateInput(attrs={"type": "date"}),
            "next_maintenance_date": forms.DateInput(attrs={"type": "date"}),
            "technical_specs": forms.Textarea(attrs={"rows": 3}),
            "accessories_included": forms.Textarea(attrs={"rows": 2}),
            "important_notes": forms.Textarea(attrs={"rows": 2}),
            "maintenance_notes": forms.Textarea(attrs={"rows": 2}),
        }


class ReservationAdminForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = (
            "user",
            "studio",
            "equipments",
            "service",
            "start_datetime",
            "end_datetime",
            "status",
            "admin_comment",
            "assigned_technician",
        )
        widgets = {
            "start_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "admin_comment": forms.Textarea(attrs={"rows": 3}),
        }


class ReservationCreateForm(forms.ModelForm):
    """
    Formulaire utilisé par l'utilisateur pour créer une réservation générale
    (studio + équipements + service).
    """

    class Meta:
        model = Reservation
        fields = (
            "studio",
            "equipments",
            "service",
            "start_datetime",
            "end_datetime",
        )
        widgets = {
            "start_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Équipements disponibles à la location
        self.fields["equipments"].queryset = Equipment.objects.filter(
            is_available_for_rent=True
        )

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_datetime")
        end = cleaned_data.get("end_datetime")

        if start and end:
            if start >= end:
                raise ValidationError(
                    "La date/heure de début doit être avant la date/heure de fin."
                )
            if start < timezone.now():
                raise ValidationError(
                    "La date/heure de début doit être dans le futur."
                )

        return cleaned_data


class EquipmentReservationForm(forms.ModelForm):
    """
    Formulaire simplifié pour réserver un matériel précis.
    On ne demande que les dates de début/fin.
    """

    class Meta:
        model = Reservation
        fields = ("start_datetime", "end_datetime")
        widgets = {
            "start_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_datetime")
        end = cleaned_data.get("end_datetime")

        if start and end:
            if start >= end:
                raise ValidationError(
                    "La date/heure de début doit être avant la date/heure de fin."
                )
            if start < timezone.now():
                raise ValidationError(
                    "La date/heure de début doit être dans le futur."
                )

        return cleaned_data


class StudioReservationForm(forms.ModelForm):
    """
    Formulaire simplifié pour réserver un studio précis.
    - Type d'événement
    - Nombre de personnes
    - Message / détails du projet
    Les infos supplémentaires seront stockées dans Reservation.admin_comment.
    """

    EVENT_TYPE_CHOICES = [
        ("", "Choisir..."),
        ("RECORDING", "Enregistrement"),
        ("REHEARSAL", "Répétition"),
        ("PODCAST", "Podcast"),
        ("DJ_SET", "DJ / Live mix"),
        ("OTHER", "Autre"),
    ]

    event_type = forms.ChoiceField(
        label="Type d’événement",
        choices=EVENT_TYPE_CHOICES,
        required=False,
        help_text="Ex : enregistrement, répétition, podcast, DJ set…",
    )

    guests_count = forms.IntegerField(
        label="Nombre de personnes",
        min_value=1,
        required=False,
        help_text="Nombre approximatif de personnes présentes dans le studio.",
    )

    message = forms.CharField(
        label="Message / détails du projet",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
        help_text="Optionnel : précisez le type d'événement, besoins spécifiques, nombre de caméras, etc.",
    )

    class Meta:
        model = Reservation
        fields = ("start_datetime", "end_datetime", "event_type", "guests_count", "message")
        widgets = {
            "start_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_datetime")
        end = cleaned_data.get("end_datetime")

        if start and end:
            if start >= end:
                raise ValidationError(
                    "La date/heure de début doit être avant la date/heure de fin."
                )
            if start < timezone.now():
                raise ValidationError(
                    "La date/heure de début doit être dans le futur."
                )

        return cleaned_data

class StudioForm(forms.ModelForm):
    """
    Formulaire pour créer / modifier un Studio (dashboard admin).
    """
    class Meta:
        model = Studio
        fields = (
            # Infos de base
            "name",
            "code",
            "studio_type",
            "description",
            # Localisation
            "address",
            "city",
            "country",
            "image",
            # Dimensions
            "length_m",
            "width_m",
            "height_m",
            "area_m2",
            # Éclairage
            "lighting_included",
            "lighting_type",
            # Équipements inclus
            "equip_cameras",
            "equip_microphones",
            "equip_lights",
            "equip_screens",
            "equip_control_room",
            "equip_accessories",
            # Tarification
            "price_per_hour",
            "price_half_day",
            "price_day",
            "extra_options",
            "discount_percent",
            # Disponibilités
            "opening_hours",
            "opening_days",
            "unavailable_dates",
            # Capacité
            "capacity",
            "technicians_required",
            # Statut global
            "status",
            "is_active",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "lighting_type": forms.Textarea(attrs={"rows": 2}),
            "equip_cameras": forms.Textarea(attrs={"rows": 2}),
            "equip_microphones": forms.Textarea(attrs={"rows": 2}),
            "equip_lights": forms.Textarea(attrs={"rows": 2}),
            "equip_screens": forms.Textarea(attrs={"rows": 2}),
            "equip_control_room": forms.Textarea(attrs={"rows": 2}),
            "equip_accessories": forms.Textarea(attrs={"rows": 2}),
            "extra_options": forms.Textarea(attrs={"rows": 2}),
            "unavailable_dates": forms.Textarea(attrs={"rows": 2}),
        }