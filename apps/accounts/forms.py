from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import (
    User,
    EmployeeProfile,
    GenderChoices,
    ContractTypeChoices,
    EducationLevelChoices,
)


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        )


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone", "avatar")


# ---------- FORMULAIRES EMPLOYÉS (ADMIN) ----------

class EmployeeCreateForm(UserCreationForm):
    """
    Formulaire pour créer un employé depuis le dashboard admin.
    Gère User + EmployeeProfile.
    """
    email = forms.EmailField(required=True, label="Email")

    role = forms.ChoiceField(
        label="Rôle",
        choices=[
            (User.Role.SUPERADMIN, "Super Administrateur"),
            (User.Role.MANAGER, "Manager"),
            (User.Role.TECHNICIAN, "Technicien"),
            (User.Role.MODERATOR, "Modérateur"),
        ],
    )
    is_staff = forms.BooleanField(
        required=False,
        initial=True,
        label="Accès à l'administration",
    )
    is_employee = forms.BooleanField(
        required=False,
        initial=True,
        label="Marquer comme employé",
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label="Compte actif",
    )

    # 1. Données personnelles
    gender = forms.ChoiceField(
        label="Genre",
        choices=[('', '---------')] + list(GenderChoices.choices),
        required=False,
    )
    date_of_birth = forms.DateField(
        label="Date de naissance",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    address = forms.CharField(label="Adresse", required=False)
    city = forms.CharField(label="Ville", required=False)
    position = forms.CharField(label="Poste occupé / recherché", required=False)

    # 2. Infos contractuelles
    salary = forms.DecimalField(
        label="Salaire",
        required=False,
        max_digits=10,
        decimal_places=2,
    )
    contract_type = forms.ChoiceField(
        label="Type de contrat",
        choices=[('', '---------')] + list(ContractTypeChoices.choices),
        required=False,
    )
    contract_document = forms.FileField(
        label="Document de contrat",
        required=False,
    )
    years_of_experience = forms.IntegerField(
        label="Années d'expérience",
        required=False,
        min_value=0,
    )
    education_level = forms.ChoiceField(
        label="Niveau d'études",
        choices=[('', '---------')] + list(EducationLevelChoices.choices),
        required=False,
    )
    diploma = forms.CharField(
        label="Diplômes principaux",
        required=False,
    )

    # 3. Contacts personnels (complémentaires)
    linkedin_url = forms.URLField(label="LinkedIn", required=False)
    facebook_url = forms.URLField(label="Facebook", required=False)
    twitter_url = forms.URLField(label="Twitter / X", required=False)
    instagram_url = forms.URLField(label="Instagram", required=False)

    # 4. Données administratives
    hire_date = forms.DateField(
        label="Date d'embauche",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    contract_end_date = forms.DateField(
        label="Fin de contrat",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    manager = forms.ModelChoiceField(
        label="Manager",
        queryset=User.objects.filter(is_employee=True),
        required=False,
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_staff",
            "is_employee",
            "is_active",
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.role = self.cleaned_data["role"]
        user.is_staff = self.cleaned_data["is_staff"]
        user.is_employee = self.cleaned_data["is_employee"]
        user.is_active = self.cleaned_data["is_active"]

        if commit:
            user.save()
            # Créer le profil employé
            EmployeeProfile.objects.create(
                user=user,
                position=self.cleaned_data.get("position", ""),
                gender=self.cleaned_data.get("gender") or "",
                date_of_birth=self.cleaned_data.get("date_of_birth"),
                address=self.cleaned_data.get("address", ""),
                city=self.cleaned_data.get("city", ""),
                salary=self.cleaned_data.get("salary"),
                contract_type=self.cleaned_data.get("contract_type") or "",
                contract_document=self.cleaned_data.get("contract_document"),
                years_of_experience=self.cleaned_data.get("years_of_experience"),
                education_level=self.cleaned_data.get("education_level") or "",
                diploma=self.cleaned_data.get("diploma", ""),
                linkedin_url=self.cleaned_data.get("linkedin_url", ""),
                facebook_url=self.cleaned_data.get("facebook_url", ""),
                twitter_url=self.cleaned_data.get("twitter_url", ""),
                instagram_url=self.cleaned_data.get("instagram_url", ""),
                hire_date=self.cleaned_data.get("hire_date"),
                contract_end_date=self.cleaned_data.get("contract_end_date"),
                manager=self.cleaned_data.get("manager"),
            )
        return user
    


class EmployeeUpdateForm(forms.ModelForm):
    """
    Formulaire pour modifier un employé depuis le dashboard admin (User + EmployeeProfile).
    """
    role = forms.ChoiceField(
        label="Rôle",
        choices=[
            (User.Role.SUPERADMIN, "Super Administrateur"),
            (User.Role.MANAGER, "Manager"),
            (User.Role.TECHNICIAN, "Technicien"),
            (User.Role.MODERATOR, "Modérateur"),
        ],
    )

    # Champs du profil employé (mêmes que pour la création)
    gender = forms.ChoiceField(
        label="Genre",
        choices=[('', '---------')] + list(GenderChoices.choices),
        required=False,
    )
    date_of_birth = forms.DateField(
        label="Date de naissance",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    address = forms.CharField(label="Adresse", required=False)
    city = forms.CharField(label="Ville", required=False)
    position = forms.CharField(label="Poste occupé / recherché", required=False)
    salary = forms.DecimalField(
        label="Salaire",
        required=False,
        max_digits=10,
        decimal_places=2,
    )
    contract_type = forms.ChoiceField(
        label="Type de contrat",
        choices=[('', '---------')] + list(ContractTypeChoices.choices),
        required=False,
    )
    contract_document = forms.FileField(
        label="Document de contrat",
        required=False,
    )
    years_of_experience = forms.IntegerField(
        label="Années d'expérience",
        required=False,
        min_value=0,
    )
    education_level = forms.ChoiceField(
        label="Niveau d'études",
        choices=[('', '---------')] + list(EducationLevelChoices.choices),
        required=False,
    )
    diploma = forms.CharField(
        label="Diplômes principaux",
        required=False,
    )
    linkedin_url = forms.URLField(label="LinkedIn", required=False)
    facebook_url = forms.URLField(label="Facebook", required=False)
    twitter_url = forms.URLField(label="Twitter / X", required=False)
    instagram_url = forms.URLField(label="Instagram", required=False)
    hire_date = forms.DateField(
        label="Date d'embauche",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    contract_end_date = forms.DateField(
        label="Fin de contrat",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    manager = forms.ModelChoiceField(
        label="Manager",
        queryset=User.objects.filter(is_employee=True),
        required=False,
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "is_staff",
            "is_employee",
            "is_active",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pré-remplir avec les données du profil employé s'il existe
        try:
            profile = self.instance.employee_profile
        except EmployeeProfile.DoesNotExist:
            profile = None

        if profile:
            self.fields['position'].initial = profile.position
            self.fields['gender'].initial = profile.gender
            self.fields['date_of_birth'].initial = profile.date_of_birth
            self.fields['address'].initial = profile.address
            self.fields['city'].initial = profile.city
            self.fields['salary'].initial = profile.salary
            self.fields['contract_type'].initial = profile.contract_type
            self.fields['years_of_experience'].initial = profile.years_of_experience
            self.fields['education_level'].initial = profile.education_level
            self.fields['diploma'].initial = profile.diploma
            self.fields['linkedin_url'].initial = profile.linkedin_url
            self.fields['facebook_url'].initial = profile.facebook_url
            self.fields['twitter_url'].initial = profile.twitter_url
            self.fields['instagram_url'].initial = profile.instagram_url
            self.fields['hire_date'].initial = profile.hire_date
            self.fields['contract_end_date'].initial = profile.contract_end_date
            self.fields['manager'].initial = profile.manager

    def save(self, commit=True):
        user = super().save(commit=commit)
        # Récupérer ou créer le profil employé
        profile, _ = EmployeeProfile.objects.get_or_create(user=user)
        cd = self.cleaned_data

        profile.position = cd.get("position", "")
        profile.gender = cd.get("gender") or ""
        profile.date_of_birth = cd.get("date_of_birth")
        profile.address = cd.get("address", "")
        profile.city = cd.get("city", "")
        profile.salary = cd.get("salary")
        profile.contract_type = cd.get("contract_type") or ""
        if cd.get("contract_document"):
            profile.contract_document = cd["contract_document"]
        profile.years_of_experience = cd.get("years_of_experience")
        profile.education_level = cd.get("education_level") or ""
        profile.diploma = cd.get("diploma", "")
        profile.linkedin_url = cd.get("linkedin_url", "")
        profile.facebook_url = cd.get("facebook_url", "")
        profile.twitter_url = cd.get("twitter_url", "")
        profile.instagram_url = cd.get("instagram_url", "")
        profile.hire_date = cd.get("hire_date")
        profile.contract_end_date = cd.get("contract_end_date")
        profile.manager = cd.get("manager")

        if commit:
            profile.save()

        return user