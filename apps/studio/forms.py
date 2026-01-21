# apps/studio/forms.py
from datetime import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .choices import ReservationStatus
from .models import Equipment, Reservation, Studio


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = (
            "name",
            "brand",
            "model",
            "category",
            "serial_number",
            "purchase_date",
            "purchase_price",
            "status",
            "is_available_for_rent",
            "current_user",
            "location",
            "technical_specs",
            "accessories_included",
            "important_notes",
            "last_maintenance_date",
            "next_maintenance_date",
            "maintenance_notes",
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
    Formulaire générique (studio + équipements + service)
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
        self.fields["equipments"].queryset = Equipment.objects.filter(is_available_for_rent=True)

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_datetime")
        end = cleaned_data.get("end_datetime")

        if start and end:
            if start >= end:
                raise ValidationError("La date/heure de début doit être avant la date/heure de fin.")
            if start < timezone.now():
                raise ValidationError("La date/heure de début doit être dans le futur.")
        return cleaned_data


class EquipmentReservationForm(forms.ModelForm):
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
                raise ValidationError("La date/heure de début doit être avant la date/heure de fin.")
            if start < timezone.now():
                raise ValidationError("La date/heure de début doit être dans le futur.")
        return cleaned_data


class StudioReservationForm(forms.ModelForm):
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
                raise ValidationError("La date/heure de début doit être avant la date/heure de fin.")
            if start < timezone.now():
                raise ValidationError("La date/heure de début doit être dans le futur.")
        return cleaned_data


class StudioForm(forms.ModelForm):
    class Meta:
        model = Studio
        fields = (
            "name",
            "code",
            "studio_type",
            "description",
            "address",
            "city",
            "country",
            "image",
            "length_m",
            "width_m",
            "height_m",
            "area_m2",
            "lighting_included",
            "lighting_type",
            "equip_cameras",
            "equip_microphones",
            "equip_lights",
            "equip_screens",
            "equip_control_room",
            "equip_accessories",
            "price_per_hour",
            "price_half_day",
            "price_day",
            "extra_options",
            "discount_percent",
            "opening_hours",
            "opening_days",
            "unavailable_dates",
            "capacity",
            "technicians_required",
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


# ==============================
# NOUVEAU FORMULAIRE PROJET (CORRIGÉ)
# Date + heure début + heure fin (obligatoire)
# ==============================
class ProjectReservationForm(forms.ModelForm):
    reservation_date = forms.DateField(
        label="Date",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    start_time = forms.TimeField(
        label="Heure de début",
        widget=forms.TimeInput(attrs={"type": "time", "class": "form-control"})
    )
    end_time = forms.TimeField(
        label="Heure de fin",
        widget=forms.TimeInput(attrs={"type": "time", "class": "form-control"})
    )

    class Meta:
        model = Reservation
        fields = (
            "studio",

            "contact_full_name",
            "contact_company",
            "contact_phone",
            "contact_email",
            "contact_city",
            "contact_country",

            "project_summary",
            "project_references",

            "format_type",
            "participants_count",
            "participants_details",

            "episode_duration_minutes",
            "episodes_count",
            "episodes_notes",

            "preferred_period",
            "preferred_date_1",
            "preferred_date_2",
            "scheduling_notes",

            "rental_studio_only",
            "option_custom_set",
            "option_make_up",
            "option_technical_team",
            "option_video_editing",
            "option_express_delivery",
            "support_other_details",

            "delivery_deadline",
            "specific_constraints",

            "budget_known",
            "budget_min",
            "budget_max",
            "budget_notes",

            "contact_pref_call",
            "contact_pref_meeting",
            "contact_pref_email_quote",

            "client_additional_message",
        )
        widgets = {
            "project_summary": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "project_references": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "participants_details": forms.TextInput(attrs={"class": "form-control"}),
            "episodes_notes": forms.TextInput(attrs={"class": "form-control"}),

            # DateTime préférées (si tu veux un rendu propre)
            "preferred_date_1": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "preferred_date_2": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),

            "scheduling_notes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "support_other_details": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "specific_constraints": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "budget_notes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "client_additional_message": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        }

    def __init__(self, *args, studio=None, **kwargs):
        self.locked_studio = studio
        super().__init__(*args, **kwargs)

        self.fields["studio"].queryset = Studio.objects.filter(is_active=True)
        self.fields["studio"].required = True

        # Si on vient d'un studio précis : on cache le champ studio, mais il sera envoyé
        if self.locked_studio is not None:
            self.fields["studio"].initial = self.locked_studio
            self.fields["studio"].widget = forms.HiddenInput()

        # Ajout "form-control" aux champs simples si besoin (optionnel mais propre)
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.NumberInput, forms.Select)):
                css = field.widget.attrs.get("class", "")
                if "form-control" not in css:
                    field.widget.attrs["class"] = (css + " form-control").strip()

    def clean(self):
        cleaned_data = super().clean()

        studio = self.locked_studio or cleaned_data.get("studio")
        date = cleaned_data.get("reservation_date")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if not (date and start_time and end_time):
            raise ValidationError("Veuillez renseigner la date, l'heure de début et l'heure de fin.")

        tz = timezone.get_current_timezone()
        start_dt = timezone.make_aware(datetime.combine(date, start_time), tz)
        end_dt = timezone.make_aware(datetime.combine(date, end_time), tz)

        if start_dt >= end_dt:
            raise ValidationError("L'heure de début doit être avant l'heure de fin.")
        if start_dt < timezone.now():
            raise ValidationError("La réservation doit être dans le futur.")

        # Anti double réservation studio (PENDING + CONFIRMED)
        conflict = Reservation.objects.filter(
            studio=studio,
            status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED],
            start_datetime__lt=end_dt,
            end_datetime__gt=start_dt,
        ).exclude(pk=self.instance.pk).exists()

        if conflict:
            raise ValidationError("Ce créneau est déjà réservé pour ce studio. Choisissez un autre horaire.")

        cleaned_data["start_datetime"] = start_dt
        cleaned_data["end_datetime"] = end_dt
        return cleaned_data

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.start_datetime = self.cleaned_data["start_datetime"]
        obj.end_datetime = self.cleaned_data["end_datetime"]

        if self.locked_studio is not None:
            obj.studio = self.locked_studio

        if commit:
            obj.save()
        return obj