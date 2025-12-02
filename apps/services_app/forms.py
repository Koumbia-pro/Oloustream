from django import forms
from .models import (
    Service, Offer, Training, Partner, OfferApplication,
    ServiceCategory, TrainingCategory,
    ServiceTypeChoices, LocationTypeChoices, DifficultyLevelChoices,
    TrainingLevelChoices, TrainingModeChoices, PartnershipTypeChoices
)


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = (
            # Infos de base
            'name',
            'slug',
            'short_description',
            'description',
            'category',
            'service_type',
            # Tarification & durée
            'base_price',
            'duration_min_minutes',
            'duration_max_minutes',
            # Logistique & complexité
            'location_type',
            'difficulty_level',
            'requires_studio',
            'requires_equipment_rental',
            # Média & statut
            'image',
            'is_active',
            # Notes internes
            'internal_notes',
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'internal_notes': forms.Textarea(attrs={'rows': 3}),
        }

class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = (
            'service',
            'title',
            'description',
            'discount_percent',
            'start_date',
            'end_date',
            'is_active',
        )
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        discount = cleaned_data.get('discount_percent')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        # Vérifier la réduction
        if discount is not None:
            if discount < 0 or discount > 100:
                self.add_error('discount_percent', "La réduction doit être entre 0 et 100 %.")

        # Vérifier les dates
        if start_date and end_date:
            if end_date < start_date:
                self.add_error('end_date', "La date de fin doit être supérieure ou égale à la date de début.")

        return cleaned_data


class TrainingForm(forms.ModelForm):
    class Meta:
        model = Training
        fields = (
            # Base
            'title',
            'slug',
            'short_description',
            'description',
            'category',
            'level',
            'mode',
            'location',
            # Pédagogie
            'objectives',
            'prerequisites',
            'target_audience',
            'program',
            # Logistique & tarif
            'duration_hours',
            'price',
            'certification',
            'max_seats',
            # Calendrier
            'start_date',
            'end_date',
            'schedule',
            # Média & statut
            'image',
            'brochure',
            'is_active',
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'objectives': forms.Textarea(attrs={'rows': 3}),
            'prerequisites': forms.Textarea(attrs={'rows': 3}),
            'target_audience': forms.Textarea(attrs={'rows': 3}),
            'program': forms.Textarea(attrs={'rows': 4}),
            'schedule': forms.Textarea(attrs={'rows': 3}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class PartnerForm(forms.ModelForm):
    class Meta:
        model = Partner
        fields = (
            'name',
            'logo',
            'website',
            'contact_name',
            'contact_email',
            'contact_phone',
            'partnership_type',
            'address',
            'notes',
            'active',
        )
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class OfferApplicationForm(forms.ModelForm):
    class Meta:
        model = OfferApplication
        fields = ('message',)
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }