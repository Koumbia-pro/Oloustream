from django import forms
from django.db import models

from .models import ContactRequest, Testimonial, VideoRealisation
from .validators import UploadValidationMixin, validate_image


def https_formfield(db_field, **kwargs):
    """Champs « lien web » : un lien saisi sans protocole est complété en https://."""
    if isinstance(db_field, models.URLField):
        kwargs.setdefault("assume_scheme", "https")
    return db_field.formfield(**kwargs)


class BootstrapFormMixin:
    """Ajoute automatiquement les classes Bootstrap aux widgets du formulaire."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.RadioSelect, forms.CheckboxSelectMultiple)):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")


class ContactRequestForm(forms.ModelForm):
    # Champ piège invisible : les robots le remplissent, les humains non.
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={
        "tabindex": "-1", "autocomplete": "off",
    }))

    class Meta:
        model = ContactRequest
        fields = ("full_name", "company", "email", "phone", "subject", "event_date", "budget", "message")
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Prénom et nom", "autocomplete": "name"}),
            "company": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nom de l’entreprise (facultatif)", "autocomplete": "organization"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "vous@exemple.com", "autocomplete": "email"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "+226 …", "autocomplete": "tel"}),
            "subject": forms.Select(attrs={"class": "form-select"}),
            "event_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "budget": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex. 500 000 FCFA"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 5,
                                             "placeholder": "Décrivez votre projet : type d'événement, lieu, durée, besoins…"}),
        }

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Requête invalide.")
        return ""

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError("Merci de décrire votre demande en quelques mots.")
        return message[:5000]


class VideoRealisationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = VideoRealisation
        fields = ("youtube_url", "title", "subtitle", "description", "tags",
                  "category", "show_on_home", "is_published", "order")
        widgets = {
            "youtube_url": forms.TextInput(attrs={"placeholder": "https://youtu.be/…", "autocomplete": "off"}),
            "title": forms.TextInput(attrs={"placeholder": "Titre de la vidéo"}),
            "subtitle": forms.TextInput(attrs={"placeholder": "Portrait · Entrepreneuriat"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "tags": forms.TextInput(attrs={"placeholder": "Portrait, Production"}),
        }


class TestimonialForm(BootstrapFormMixin, UploadValidationMixin, forms.ModelForm):
    upload_rules = {"photo": validate_image}

    class Meta:
        model = Testimonial
        fields = ("quote", "author_name", "author_role", "organization", "photo", "is_published", "order")
        widgets = {
            "quote": forms.Textarea(attrs={"rows": 4, "placeholder": "Grâce à Oloustream, nous avons…"}),
            "author_name": forms.TextInput(attrs={"placeholder": "Awa Ouédraogo"}),
            "author_role": forms.TextInput(attrs={"placeholder": "Responsable communication"}),
            "organization": forms.TextInput(attrs={"placeholder": "Nom de la structure"}),
        }
