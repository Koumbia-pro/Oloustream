# apps/studio/choices.py
from django.db import models


class EquipmentStatus(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Disponible'
    IN_USE = 'IN_USE', 'En utilisation'
    MAINTENANCE = 'MAINTENANCE', 'En maintenance'
    OUT_OF_SERVICE = 'OUT_OF_SERVICE', 'Hors service'
    RETIRED = 'RETIRED', 'Retiré'


class ReservationStatus(models.TextChoices):
    PENDING = 'PENDING', 'En attente'
    CONFIRMED = 'CONFIRMED', 'Confirmée'
    REJECTED = 'REJECTED', 'Refusée'
    CANCELLED = 'CANCELLED', 'Annulée'
    COMPLETED = 'COMPLETED', 'Terminée'


class StudioTypeChoices(models.TextChoices):
    VIDEO = "VIDEO", "Studio vidéo"
    AUDIO = "AUDIO", "Studio audio / podcast"
    PHOTO = "PHOTO", "Studio photo"
    MULTI = "MULTI", "Multi-usage"


class StudioStatusChoices(models.TextChoices):
    AVAILABLE = "AVAILABLE", "Disponible"
    UNAVAILABLE = "UNAVAILABLE", "Indisponible"
    MAINTENANCE = "MAINTENANCE", "En maintenance"