from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        SUPERADMIN = 'SUPERADMIN', 'Super Administrateur'
        MANAGER = 'MANAGER', 'Manager'
        TECHNICIAN = 'TECHNICIAN', 'Technicien'
        MODERATOR = 'MODERATOR', 'Modérateur'
        CLIENT = 'CLIENT', 'Client'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT,
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True)
    is_employee = models.BooleanField(default=False)

    def is_admin_role(self):
        return self.role in {self.Role.SUPERADMIN, self.Role.MANAGER, self.Role.MODERATOR}


# ====== CHOIX POUR LES EMPLOYÉS ======

class GenderChoices(models.TextChoices):
    MALE = 'M', 'Homme'
    FEMALE = 'F', 'Femme'
    OTHER = 'O', 'Autre'


class ContractTypeChoices(models.TextChoices):
    CDI = 'CDI', 'CDI'
    CDD = 'CDD', 'CDD'
    INTERNSHIP = 'INTERNSHIP', 'Stage'
    FREELANCE = 'FREELANCE', 'Freelance'
    OTHER = 'OTHER', 'Autre'


class EducationLevelChoices(models.TextChoices):
    HIGH_SCHOOL = 'HIGH_SCHOOL', 'Bac ou moins'
    BACHELOR = 'BACHELOR', 'Licence / Bachelor'
    MASTER = 'MASTER', 'Master'
    DOCTORATE = 'DOCTORATE', 'Doctorat'
    OTHER = 'OTHER', 'Autre'


class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')

    # 1. Données personnelles
    position = models.CharField("Poste occupé / recherché", max_length=100, blank=True)
    gender = models.CharField("Genre", max_length=1, choices=GenderChoices.choices, blank=True)
    date_of_birth = models.DateField("Date de naissance", blank=True, null=True)
    address = models.CharField("Adresse", max_length=255, blank=True)
    city = models.CharField("Ville", max_length=100, blank=True)
    bio = models.TextField("Bio / Notes internes", blank=True)

    # 2. Infos contractuelles
    salary = models.DecimalField("Salaire (brut / net)", max_digits=10, decimal_places=2, blank=True, null=True)
    contract_type = models.CharField("Type de contrat", max_length=20, choices=ContractTypeChoices.choices, blank=True)
    contract_document = models.FileField("Document de contrat", upload_to='contracts/', blank=True, null=True)
    years_of_experience = models.PositiveIntegerField("Années d'expérience", blank=True, null=True)
    education_level = models.CharField("Niveau d'études", max_length=20, choices=EducationLevelChoices.choices, blank=True)
    diploma = models.CharField("Diplômes principaux", max_length=255, blank=True)

    # 3. Contacts personnels (email & téléphone sont sur User)
    linkedin_url = models.URLField("LinkedIn", blank=True)
    facebook_url = models.URLField("Facebook", blank=True)
    twitter_url = models.URLField("Twitter / X", blank=True)
    instagram_url = models.URLField("Instagram", blank=True)

    # 4. Données administratives
    hire_date = models.DateField("Date d'embauche", blank=True, null=True)
    contract_end_date = models.DateField("Fin de contrat", blank=True, null=True)
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_employees',
        verbose_name="Manager",
        limit_choices_to={'is_employee': True},
    )

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.position or 'Employé'}"