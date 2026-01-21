# apps/studio/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required

from .forms import (
    ReservationCreateForm,
    EquipmentReservationForm,
    ProjectReservationForm,
)
from .models import Reservation, Equipment, Studio
from .choices import ReservationStatus, EquipmentStatus
from .services import log_reservation_status_change
from apps.notifications.services import notify_admins_new_reservation
from apps.notifications.emailing import send_reservation_received_email, send_reservation_status_changed_email


# ---------- RÉSERVATIONS UTILISATEUR ----------

@login_required
def user_reservation_list_view(request):
    reservations = Reservation.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "user/reservations/list.html", {"reservations": reservations})


@login_required
def user_reservation_create_view(request):
    if request.method == "POST":
        form = ReservationCreateForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.status = ReservationStatus.PENDING
            reservation.save()
            form.save_m2m()

            log_reservation_status_change(
                reservation=reservation,
                old_status=ReservationStatus.PENDING,
                new_status=ReservationStatus.PENDING,
                changed_by=request.user,
                note="Création de la réservation par l'utilisateur.",
                force=True,
            )

            notify_admins_new_reservation(reservation)

            messages.success(request, "Votre réservation a été créée et est en attente de validation.")
            return redirect("studio:user_reservations_list")
    else:
        form = ReservationCreateForm()

    return render(request, "user/reservations/create.html", {"form": form})


# ---------- MATÉRIEL ----------

@login_required
def user_equipment_list_view(request):
    equipments = Equipment.objects.filter(
        is_available_for_rent=True,
        status=EquipmentStatus.AVAILABLE,
    ).select_related("category")
    return render(request, "user/equipments/list.html", {"equipments": equipments})


@login_required
def user_equipment_detail_view(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    return render(request, "user/equipments/detail.html", {"equipment": equipment})


@login_required
def user_equipment_reserve_view(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)

    if not equipment.is_available_for_rent or equipment.status != EquipmentStatus.AVAILABLE:
        messages.error(request, "Cet équipement n'est pas disponible à la location pour le moment.")
        return redirect("studio:user_equipment_detail", pk=equipment.pk)

    if request.method == "POST":
        form = EquipmentReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.status = ReservationStatus.PENDING
            reservation.save()
            reservation.equipments.add(equipment)

            log_reservation_status_change(
                reservation=reservation,
                old_status=ReservationStatus.PENDING,
                new_status=ReservationStatus.PENDING,
                changed_by=request.user,
                note=f"Réservation de matériel '{equipment.name}' par l'utilisateur.",
                force=True,
            )

            notify_admins_new_reservation(reservation)

            messages.success(request, "Votre demande de réservation a été envoyée et est en attente de validation.")
            return redirect("studio:user_reservations_list")
    else:
        form = EquipmentReservationForm()

    return render(request, "user/equipments/reserve.html", {"equipment": equipment, "form": form})


# ---------- STUDIOS ----------

def user_studio_list_view(request):
    studios = Studio.objects.filter(is_active=True).order_by("name")
    return render(request, "user/studios/list.html", {"studios": studios})


@login_required
def user_studio_detail_view(request, pk):
    studio = get_object_or_404(Studio, pk=pk, is_active=True)
    return render(request, "user/studios/detail.html", {"studio": studio})


@login_required
def user_studio_reserve_view(request, pk):
    """
    Redirection vers le formulaire projet complet (studio pré-sélectionné).
    """
    studio = get_object_or_404(Studio, pk=pk, is_active=True)
    return redirect("studio:user_studio_project_reservation", studio_pk=studio.pk)


# ---------- FORMULAIRE PROJET (GLOBAL OU STUDIO PRÉ-SÉLECTIONNÉ) ----------

@login_required
def user_project_reservation_create_view(request, studio_pk=None):
    studio = None
    if studio_pk is not None:
        studio = get_object_or_404(Studio, pk=studio_pk, is_active=True)

    if request.method == "POST":
        form = ProjectReservationForm(request.POST, studio=studio)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.status = ReservationStatus.PENDING
            reservation.save()

            log_reservation_status_change(
                reservation=reservation,
                old_status=ReservationStatus.PENDING,
                new_status=ReservationStatus.PENDING,
                changed_by=request.user,
                note="Création de la réservation via formulaire projet.",
                force=True,
            )

            notify_admins_new_reservation(reservation)
            send_reservation_received_email(request, reservation)

            messages.success(
                request,
                "Votre demande a été envoyée et est en attente de validation. "
                "Un conseiller vous contactera si nécessaire.",
            )
            return redirect("studio:user_reservations_list")
    else:
        form = ProjectReservationForm(studio=studio)

    return render(request, "user/reservations/project_create.html", {"form": form, "studio": studio})


# ---------- ADMIN (STAFF) ----------

@staff_member_required
def admin_reservation_list_view(request):
    reservations = (
        Reservation.objects
        .select_related("user", "studio", "service")
        .order_by("-created_at")
    )

    status_filter = request.GET.get("status")
    if status_filter:
        reservations = reservations.filter(status=status_filter)

    return render(
        request,
        "admin/reservations/list.html",
        {"reservations": reservations, "status_filter": status_filter},
    )


@staff_member_required
def admin_reservation_detail_view(request, pk):
    reservation = get_object_or_404(
        Reservation.objects.select_related("user", "studio", "service"),
        pk=pk,
    )
    history = reservation.status_history.select_related("changed_by").all()

    return render(
        request,
        "admin/reservations/detail.html",
        {"reservation": reservation, "history": history},
    )