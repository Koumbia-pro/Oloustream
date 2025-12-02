# apps/studio/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .forms import (
    ReservationCreateForm,
    EquipmentReservationForm,
    StudioReservationForm,
)
from .models import Reservation, Equipment, ReservationStatusHistory, Studio
from .choices import ReservationStatus, EquipmentStatus
from .services import log_reservation_status_change
from apps.notifications.services import notify_admins_new_reservation
from django.urls import reverse


# ---------- RÉSERVATIONS GÉNÉRALES (studio + équipements) ----------

@login_required
def user_reservation_list_view(request):
    """
    Liste des réservations de l'utilisateur connecté.
    """
    reservations = Reservation.objects.filter(user=request.user).order_by("-created_at")
    return render(
        request,
        "user/reservations/list.html",
        {"reservations": reservations},
    )


@login_required
def user_reservation_create_view(request):
    """
    Formulaire générique de création de réservation (studio + équipements + service).
    """
    if request.method == "POST":
        form = ReservationCreateForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.status = ReservationStatus.PENDING
            reservation.save()
            form.save_m2m()

            # Historique initial
            log_reservation_status_change(
                reservation=reservation,
                old_status=ReservationStatus.PENDING,
                new_status=ReservationStatus.PENDING,
                changed_by=request.user,
                note="Création de la réservation par l'utilisateur.",
            )

            # Notification aux admins
            notify_admins_new_reservation(reservation)

            messages.success(
                request,
                "Votre réservation a été créée et est en attente de validation.",
            )
            return redirect("studio:user_reservations_list")
    else:
        form = ReservationCreateForm()

    return render(
        request,
        "user/reservations/create.html",
        {"form": form},
    )


# ---------- MATÉRIEL : liste, détail, réservation ----------

@login_required
def user_equipment_list_view(request):
    """
    Liste du matériel disponible à la location, regroupé par catégorie.
    """
    equipments = Equipment.objects.filter(
        is_available_for_rent=True,
        status=EquipmentStatus.AVAILABLE,
    ).select_related("category")

    return render(
        request,
        "user/equipments/list.html",
        {"equipments": equipments},
    )


@login_required
def user_equipment_detail_view(request, pk):
    """
    Détail d'un équipement (vue utilisateur).
    """
    equipment = get_object_or_404(Equipment, pk=pk)
    return render(
        request,
        "user/equipments/detail.html",
        {"equipment": equipment},
    )


@login_required
def user_equipment_reserve_view(request, pk):
    """
    Réserver un équipement précis.
    """
    equipment = get_object_or_404(Equipment, pk=pk)

    if not equipment.is_available_for_rent or equipment.status != EquipmentStatus.AVAILABLE:
        messages.error(
            request,
            "Cet équipement n'est pas disponible à la location pour le moment.",
        )
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
            )

            notify_admins_new_reservation(reservation)

            messages.success(
                request,
                "Votre demande de réservation a été envoyée et est en attente de validation.",
            )
            return redirect("studio:user_reservations_list")
    else:
        form = EquipmentReservationForm()

    return render(
        request,
        "user/equipments/reserve.html",
        {
            "equipment": equipment,
            "form": form,
        },
    )


# ---------- STUDIOS : liste, détail, réservation ----------

# @login_required
def user_studio_list_view(request):
    """
    Liste des studios disponibles.
    """
    studios = Studio.objects.filter(is_active=True).order_by("name")
    return render(
        request,
        "user/studios/list.html",
        {"studios": studios},
    )


@login_required
def user_studio_detail_view(request, pk):
    """
    Détail d'un studio (vue utilisateur).
    """
    studio = get_object_or_404(Studio, pk=pk, is_active=True)
    return render(
        request,
        "user/studios/detail.html",
        {"studio": studio},
    )


@login_required
def user_studio_reserve_view(request, pk):
    """
    Réserver un studio précis.
    - Page visible même sans être connecté.
    - Si POST et user non connecté -> redirection vers login + next.
    - Si connecté -> création de Reservation (PENDING) + admin_comment enrichi.
    """
    studio = get_object_or_404(Studio, pk=pk, is_active=True)

    if request.method == "POST":
        form = StudioReservationForm(request.POST)

        # Si pas connecté : on envoie vers login avec next
        if not request.user.is_authenticated:
            messages.info(request, "Connectez-vous ou créez un compte pour finaliser votre réservation.")
            login_url = reverse("accounts:login")
            return redirect(f"{login_url}?next={request.path}")

        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.studio = studio
            reservation.status = ReservationStatus.PENDING

            # Construire un commentaire admin à partir des champs du formulaire
            comment_parts = []

            event_code = form.cleaned_data.get("event_type")
            if event_code:
                label_map = dict(StudioReservationForm.EVENT_TYPE_CHOICES)
                event_label = label_map.get(event_code, event_code)
                comment_parts.append(f"Type d’événement : {event_label}")

            guests = form.cleaned_data.get("guests_count")
            if guests:
                comment_parts.append(f"Nombre de personnes : {guests}")

            message_text = form.cleaned_data.get("message")
            if message_text:
                comment_parts.append("Message utilisateur :")
                comment_parts.append(message_text)

            if comment_parts:
                reservation.admin_comment = "\n".join(comment_parts)

            reservation.save()

            # Historique initial
            log_reservation_status_change(
                reservation=reservation,
                old_status=ReservationStatus.PENDING,
                new_status=ReservationStatus.PENDING,
                changed_by=request.user,
                note=f"Réservation du studio '{studio.name}' par l'utilisateur.",
            )

            # Notification aux admins
            notify_admins_new_reservation(reservation)

            messages.success(
                request,
                "Votre demande de réservation de studio a été envoyée et est en attente de validation."
            )
            return redirect("studio:user_reservations_list")
    else:
        form = StudioReservationForm()

    return render(
        request,
        "user/studios/reserve.html",
        {
            "studio": studio,
            "form": form,
        },
    )