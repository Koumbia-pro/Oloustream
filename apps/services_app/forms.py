from django import forms

from apps.core.forms import BootstrapFormMixin
from apps.core.validators import UploadValidationMixin, validate_image, validate_pdf

from .models import (
    Service, Offer, Training, Partner, OfferApplication,
    ServiceCategory, TrainingCategory,
    ServiceTypeChoices, LocationTypeChoices, DifficultyLevelChoices,
    TrainingLevelChoices, TrainingModeChoices, PartnershipTypeChoices
)


class ServiceForm(BootstrapFormMixin, UploadValidationMixin, forms.ModelForm):
    upload_rules = {'image': validate_image}

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

class OfferForm(BootstrapFormMixin, forms.ModelForm):
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


class TrainingForm(BootstrapFormMixin, UploadValidationMixin, forms.ModelForm):
    upload_rules = {'image': validate_image, 'brochure': validate_pdf}

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


class PartnerForm(BootstrapFormMixin, UploadValidationMixin, forms.ModelForm):
    upload_rules = {'logo': validate_image}

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

class OfferApplicationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = OfferApplication
        fields = ('message',)
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }


from .models import JobApplication, JobOffer


class JobOfferForm(BootstrapFormMixin, UploadValidationMixin, forms.ModelForm):
    upload_rules = {'poster': validate_image}

    class Meta:
        model = JobOffer
        fields = (
            "status", "offer_type",
            "title", "department", "location",
            "contract_type", "level",
            "poster",
            "summary", "description",
            "responsibilities", "requirements", "benefits",
            "deadline",
        )
        widgets = {
            "deadline": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 6}),
            "responsibilities": forms.Textarea(attrs={"rows": 4}),
            "requirements": forms.Textarea(attrs={"rows": 4}),
            "benefits": forms.Textarea(attrs={"rows": 3}),
        }


class JobApplicationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ("full_name", "email", "phone", "portfolio_url", "cv", "cover_letter")
        widgets = {
            "cover_letter": forms.Textarea(attrs={"rows": 5}),
            "cv": forms.FileInput(attrs={"accept": ".pdf,application/pdf"}),
        }

    def clean_cv(self):
        f = self.cleaned_data.get("cv")
        if f and hasattr(f, "content_type"):
            validate_pdf(f, max_size_mb=5)
        return f


class JobApplicationStatusForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ("status", "internal_note")
        widgets = {"internal_note": forms.Textarea(attrs={"rows": 3})}