# apps/studio/services.py
from .choices import ReservationStatus
from .models import Reservation, ReservationStatusHistory

# Statuts qui bloquent un créneau
BLOCKING_STATUSES = [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]


def log_reservation_status_change(
    reservation: Reservation,
    old_status: str,
    new_status: str,
    changed_by=None,
    note: str = "",
    force: bool = False,
):
    """
    Crée une entrée d'historique de statut pour une réservation.
    """
    if old_status == new_status and not force:
        return

    ReservationStatusHistory.objects.create(
        reservation=reservation,
        old_status=old_status,
        new_status=new_status,
        changed_by=changed_by,
        note=(note or "")[:500],
    )


def overlapping_reservations(start, end, *, studio=None, equipments=None, exclude_pk=None,
                             statuses=None):
    """Réservations actives qui chevauchent le créneau [start, end[ pour ce studio ou ce matériel."""
    qs = Reservation.objects.filter(
        status__in=statuses or BLOCKING_STATUSES,
        start_datetime__lt=end,
        end_datetime__gt=start,
    )
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    if studio is not None and equipments:
        from django.db.models import Q
        qs = qs.filter(Q(studio=studio) | Q(equipments__in=equipments)).distinct()
    elif studio is not None:
        qs = qs.filter(studio=studio)
    elif equipments:
        qs = qs.filter(equipments__in=equipments).distinct()
    else:
        return qs.none()
    return qs


def confirmation_conflicts(reservation):
    """Réservations déjà confirmées qui empêchent de confirmer celle-ci."""
    return overlapping_reservations(
        reservation.start_datetime,
        reservation.end_datetime,
        studio=reservation.studio,
        equipments=list(reservation.equipments.all()),
        exclude_pk=reservation.pk,
        statuses=[ReservationStatus.CONFIRMED],
    )
