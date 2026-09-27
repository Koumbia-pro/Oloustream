from django.db import models


class ContactRequest(models.Model):
    """Demande de contact ou de devis envoyée depuis le site public."""

    class Subject(models.TextChoices):
        QUOTE = "QUOTE", "Demande de devis"
        STUDIO = "STUDIO", "Location de studio"
        LIVE = "LIVE", "Live streaming / captation"
        EQUIPMENT = "EQUIPMENT", "Location de matériel"
        TRAINING = "TRAINING", "Formation"
        PARTNERSHIP = "PARTNERSHIP", "Partenariat"
        OTHER = "OTHER", "Autre demande"

    class Status(models.TextChoices):
        NEW = "NEW", "Nouvelle"
        IN_PROGRESS = "IN_PROGRESS", "En cours de traitement"
        DONE = "DONE", "Traitée"

    full_name = models.CharField("Nom complet", max_length=150)
    company = models.CharField("Structure / entreprise", max_length=150, blank=True)
    email = models.EmailField("Email")
    phone = models.CharField("Téléphone", max_length=40, blank=True)
    subject = models.CharField("Objet", max_length=20, choices=Subject.choices, default=Subject.QUOTE)
    event_date = models.DateField("Date souhaitée", null=True, blank=True)
    budget = models.CharField("Budget indicatif", max_length=100, blank=True)
    message = models.TextField("Message")

    status = models.CharField("Statut", max_length=20, choices=Status.choices, default=Status.NEW)
    internal_notes = models.TextField("Notes internes", blank=True)
    ip_address = models.GenericIPAddressField("Adresse IP", null=True, blank=True)
    created_at = models.DateTimeField("Reçue le", auto_now_add=True)

    class Meta:
        verbose_name = "Demande de contact"
        verbose_name_plural = "Demandes de contact"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} — {self.get_subject_display()} ({self.created_at:%d/%m/%Y})"
