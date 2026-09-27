import datetime

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.core.utils import (
    excel_response, fmt_datetime, parse_int, querystring_without_page, safe_redirect, send_safely,
)
from apps.notifications.emailing import send_reservation_status_changed_email
from apps.notifications.services import notify_user_reservation_status_change
from apps.services_app.models import Service
from apps.studio.choices import ReservationStatus
from apps.studio.forms import ReservationAdminForm
from apps.studio.models import Reservation, Studio
from apps.studio.services import confirmation_conflicts, log_reservation_status_change

__all__ = [
    "reservation_list_view", "reservation_export_excel_view", "reservation_quick_cancel_view",
    "reservation_detail_view", "reservation_set_status_view",
]


def _status_label(value):
    try:
        return ReservationStatus(value).label
    except ValueError:
        return value


def _parse_date(value):
    try:
        return datetime.date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _filtered_reservations(request):
    qs = (
        Reservation.objects
        .select_related("user", "studio", "service", "assigned_technician")
        .prefetch_related("equipments")
        .order_by("-created_at")
    )
    filters = {
        "q": request.GET.get("q", "").strip(),
        "status": request.GET.get("status", ""),
        "studio": request.GET.get("studio", ""),
        "service": request.GET.get("service", ""),
        "date_from": request.GET.get("date_from", ""),
        "date_to": request.GET.get("date_to", ""),
    }
    if filters["q"]:
        q = filters["q"]
        search = (
            Q(user__username__icontains=q) | Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q)
            | Q(user__email__icontains=q) | Q(studio__name__icontains=q) | Q(service__name__icontains=q)
            | Q(contact_full_name__icontains=q) | Q(contact_company__icontains=q) | Q(admin_comment__icontains=q)
        )
        if q.lstrip("#").isdigit():
            search |= Q(pk=int(q.lstrip("#")))
        qs = qs.filter(search)
    if filters["status"] in ReservationStatus.values:
        qs = qs.filter(status=filters["status"])
    studio_id = parse_int(filters["studio"])
    if studio_id:
        qs = qs.filter(studio_id=studio_id)
    service_id = parse_int(filters["service"])
    if service_id:
        qs = qs.filter(service_id=service_id)
    date_from, date_to = _parse_date(filters["date_from"]), _parse_date(filters["date_to"])
    if date_from:
        qs = qs.filter(start_datetime__date__gte=date_from)
    if date_to:
        qs = qs.filter(start_datetime__date__lte=date_to)
    return qs, filters


@staff_member_required
def reservation_list_view(request):
    qs, filters = _filtered_reservations(request)
    now = timezone.now()
    stats = qs.aggregate(
        total=Count("id", distinct=True),
        pending=Count("id", filter=Q(status=ReservationStatus.PENDING), distinct=True),
        confirmed=Count("id", filter=Q(status=ReservationStatus.CONFIRMED), distinct=True),
        completed=Count("id", filter=Q(status=ReservationStatus.COMPLETED), distinct=True),
        cancelled=Count("id", filter=Q(status=ReservationStatus.CANCELLED), distinct=True),
        rejected=Count("id", filter=Q(status=ReservationStatus.REJECTED), distinct=True),
        upcoming=Count("id", filter=Q(start_datetime__gte=now), distinct=True),
        past=Count("id", filter=Q(end_datetime__lt=now), distinct=True),
    )
    return render(request, "admin/reservations/list.html", {
        "page_obj": Paginator(qs, 12).get_page(request.GET.get("page")),
        "q": filters["q"],
        "selected_status": filters["status"],
        "selected_studio": filters["studio"],
        "selected_service": filters["service"],
        "date_from": filters["date_from"],
        "date_to": filters["date_to"],
        "status_choices": ReservationStatus.choices,
        "studios": Studio.objects.order_by("name"),
        "services": Service.objects.filter(is_active=True).order_by("name"),
        "base_querystring": querystring_without_page(request),
        **{f"{key}_count": value for key, value in stats.items()},
    })


@staff_member_required
def reservation_export_excel_view(request):
    qs, _ = _filtered_reservations(request)
    rows = []
    for r in qs:
        user = r.user
        rows.append([
            r.id, r.contact_full_name or user.get_full_name() or user.username,
            r.contact_company, r.contact_email or user.email, r.contact_phone or user.phone,
            r.studio.name if r.studio else "", r.service.name if r.service else "",
            ", ".join(e.name for e in r.equipments.all()),
            fmt_datetime(r.start_datetime), fmt_datetime(r.end_datetime), r.get_status_display(),
            r.assigned_technician.get_full_name() if r.assigned_technician else "",
            fmt_datetime(r.created_at), (r.admin_comment or "")[:200],
        ])
    return excel_response(
        "reservations", "Réservations",
        ["ID", "Client", "Structure", "Email", "Téléphone", "Studio", "Service", "Matériel",
         "Début", "Fin", "Statut", "Technicien", "Créée le", "Commentaire admin"],
        rows, [6, 22, 20, 26, 16, 20, 20, 30, 17, 17, 12, 20, 17, 40],
    )


def _apply_status_change(request, reservation, new_status, note=""):
    """Change le statut, journalise, notifie le client. Retourne un message d'erreur ou None."""
    old_status = reservation.status
    if old_status == new_status:
        return "La réservation a déjà ce statut."
    if new_status == ReservationStatus.CONFIRMED:
        if reservation.end_datetime and reservation.end_datetime < timezone.now():
            return "Impossible de confirmer : ce créneau est déjà passé."
        conflict = confirmation_conflicts(reservation).first()
        if conflict:
            return (f"Impossible de confirmer : conflit avec la réservation #{conflict.pk} "
                    f"déjà confirmée sur ce créneau.")

    reservation.status = new_status
    reservation.save(update_fields=["status"])
    log_reservation_status_change(
        reservation=reservation, old_status=old_status, new_status=new_status,
        changed_by=request.user, note=note or f"Statut changé : {_status_label(new_status)}",
    )
    notify_user_reservation_status_change(
        reservation=reservation, old_status=_status_label(old_status),
        new_status=_status_label(new_status), actor=request.user,
    )
    send_safely(
        send_reservation_status_changed_email, request, reservation,
        _status_label(old_status), _status_label(new_status), admin_note=note,
    )
    return None


@staff_member_required
@require_POST
def reservation_quick_cancel_view(request, reservation_id):
    """Annulation rapide depuis la liste (POST uniquement)."""
    reservation = get_object_or_404(Reservation, pk=reservation_id)
    error = _apply_status_change(request, reservation, ReservationStatus.CANCELLED,
                                 note="Annulation rapide depuis la liste des réservations.")
    if error:
        messages.info(request, error)
    else:
        messages.success(request, f"La réservation #{reservation.id} a été annulée.")
    return redirect("dashboard:reservations_list")


@staff_member_required
@require_POST
def reservation_set_status_view(request, reservation_id):
    """Action rapide : CONFIRMED / REJECTED / COMPLETED / CANCELLED."""
    reservation = get_object_or_404(Reservation.objects.select_related("user", "studio"), pk=reservation_id)
    fallback = "dashboard:reservations_list"
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")

    new_status = request.POST.get("status", "").strip()
    allowed = {ReservationStatus.CONFIRMED, ReservationStatus.REJECTED,
               ReservationStatus.COMPLETED, ReservationStatus.CANCELLED}
    if new_status not in allowed:
        messages.error(request, "Statut invalide.")
        return safe_redirect(request, next_url, fallback)

    note = request.POST.get("note", "").strip()
    error = _apply_status_change(request, reservation, new_status, note=note)
    if error:
        messages.error(request, error)
    else:
        messages.success(request, f"Réservation #{reservation.id} : {_status_label(new_status)}.")
    return safe_redirect(request, next_url, fallback)


@staff_member_required
def reservation_detail_view(request, reservation_id):
    reservation = get_object_or_404(
        Reservation.objects
        .select_related("user", "studio", "service", "assigned_technician")
        .prefetch_related("equipments"),
        pk=reservation_id,
    )
    old_status = reservation.status

    if request.method == "POST":
        form = ReservationAdminForm(request.POST, instance=reservation)
        if form.is_valid():
            new_status = form.cleaned_data["status"]
            if new_status == ReservationStatus.CONFIRMED and old_status != new_status:
                candidate = form.save(commit=False)
                conflict = confirmation_conflicts(candidate).first()
                if conflict:
                    form.add_error("status", f"Conflit avec la réservation #{conflict.pk} déjà confirmée.")
                    # l'instance du formulaire a été modifiée : on recharge l'objet affiché
                    reservation = Reservation.objects.select_related(
                        "user", "studio", "service", "assigned_technician"
                    ).get(pk=reservation.pk)
            if not form.errors:
                updated = form.save()
                note = form.cleaned_data.get("admin_comment", "") or ""
                log_reservation_status_change(
                    reservation=updated, old_status=old_status, new_status=updated.status,
                    changed_by=request.user, note=note,
                )
                if old_status != updated.status:
                    notify_user_reservation_status_change(
                        reservation=updated, old_status=_status_label(old_status),
                        new_status=_status_label(updated.status), actor=request.user,
                    )
                    send_safely(
                        send_reservation_status_changed_email, request, updated,
                        _status_label(old_status), _status_label(updated.status), admin_note=note,
                    )
                messages.success(request, "Réservation mise à jour avec succès.")
                return redirect("dashboard:reservations_detail", reservation_id=updated.id)
    else:
        form = ReservationAdminForm(instance=reservation)

    conflicts = []
    if reservation.status in (ReservationStatus.PENDING, ReservationStatus.CONFIRMED):
        conflicts = list(confirmation_conflicts(reservation).select_related("user")[:5])

    return render(request, "admin/reservations/detail.html", {
        "reservation": reservation,
        "form": form,
        "status_history": reservation.status_history.select_related("changed_by").all(),
        "conflicts": conflicts,
        "status_choices": ReservationStatus.choices,
    })
