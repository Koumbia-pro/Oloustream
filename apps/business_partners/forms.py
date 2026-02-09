from django import forms
from .models import PartnerApplication, Contract


class PartnerApplicationForm(forms.ModelForm):
    """Formulaire de candidature partenaire"""
    
    terms_accepted = forms.BooleanField(
        required=True,
        label="J'accepte les conditions du programme de partenariat",
        error_messages={
            'required': 'Vous devez accepter les conditions pour continuer'
        }
    )
    
    class Meta:
        model = PartnerApplication
        fields = [
            'full_name', 'phone', 'email', 'whatsapp',
            'id_type', 'id_number', 'id_document',
            'city', 'address',
            'current_activity', 'experience_years',
            'network_strength', 'network_description',
            'sectors_knowledge', 'why_oloustream',
            'availability', 'references'
        ]
        
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: OUEDRAOGO Jean'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+226 XX XX XX XX'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'votre@email.com'
            }),
            'whatsapp': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+226 XX XX XX XX'
            }),
            'id_type': forms.Select(attrs={'class': 'form-control'}),
            'id_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'B123456789'
            }),
            'city': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Quartier, secteur...'
            }),
            'current_activity': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Entrepreneur, Commercial...'
            }),
            'experience_years': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 50
            }),
            'network_strength': forms.Select(attrs={'class': 'form-control'}),
            'network_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Décrivez vos contacts et votre réseau...'
            }),
            'sectors_knowledge': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ex: Événementiel, ONG, Médias...'
            }),
            'why_oloustream': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Expliquez vos motivations...'
            }),
            'availability': forms.Select(attrs={'class': 'form-control'}),
            'references': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Nom, fonction, contact (facultatif)'
            }),
        }


class ContractSubmissionForm(forms.ModelForm):
    """Formulaire pour qu'un partenaire soumette un contrat"""
    
    class Meta:
        model = Contract
        fields = [
            'client_name', 'client_type', 'client_contact',
            'service_type', 'description',
            'contract_amount', 'contract_file'
        ]
        
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }