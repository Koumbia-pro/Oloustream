# apps/studio/services.py
from .models import ReservationStatusHistory, Reservation
from .choices import ReservationStatus


def log_reservation_status_change(reservation: Reservation,
                                  old_status: str,
                                  new_status: str,
                                  changed_by=None,
                                  note: str = ""):
    """
    Crée une entrée d'historique de statut pour une réservation.

    - reservation : instance de Reservation
    - old_status  : ancien statut (string, ex: ReservationStatus.PENDING)
    - new_status  : nouveau statut
    - changed_by  : User ou None
    - note        : commentaire optionnel (tronqué à 500 chars)
    """
    if old_status == new_status:
        return

    ReservationStatusHistory.objects.create(
        reservation=reservation,
        old_status=old_status,
        new_status=new_status,
        changed_by=changed_by,
        note=(note or "")[:500],
    )