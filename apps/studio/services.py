# apps/studio/services.py
from .models import ReservationStatusHistory, Reservation


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