from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.studio.choices import ReservationStatus, StudioStatusChoices
from apps.studio.forms import StudioForm
from apps.studio.models import Studio

__all__ = ["studio_list_view", "studio_create_view", "studio_update_view", "studio_detail_view", "studio_delete_view"]


@staff_member_required
def studio_list_view(request):
    studios = Studio.objects.annotate(
        reservations_count=Count("reservation"),
        upcoming_count=Count("reservation", filter=Q(
            reservation__start_datetime__gte=timezone.now(),
            reservation__status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED],
        )),
    ).order_by("name")
    stats = Studio.objects.aggregate(
        total=Count("id"),
        available=Count("id", filter=Q(status=StudioStatusChoices.AVAILABLE)),
        maintenance=Count("id", filter=Q(status=StudioStatusChoices.MAINTENANCE)),
        unavailable=Count("id", filter=Q(status=StudioStatusChoices.UNAVAILABLE)),
    )
    return render(request, "admin/studios/list.html", {
        "studios": studios,
        "total_count": stats["total"],
        "available_count": stats["available"],
        "maintenance_count": stats["maintenance"],
        "unavailable_count": stats["unavailable"],
    })


@staff_member_required
def studio_create_view(request):
    form = StudioForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        studio = form.save()
        messages.success(request, f"Le studio « {studio.name} » a été créé avec succès.")
        return redirect("dashboard:studios_detail", studio_id=studio.pk)
    return render(request, "admin/studios/form.html", {"form": form, "studio": None})


@staff_member_required
def studio_update_view(request, studio_id):
    studio = get_object_or_404(Studio, pk=studio_id)
    form = StudioForm(request.POST or None, request.FILES or None, instance=studio)
    if request.method == "POST" and form.is_valid():
        studio = form.save()
        messages.success(request, f"Le studio « {studio.name} » a été mis à jour.")
        return redirect("dashboard:studios_detail", studio_id=studio.pk)
    return render(request, "admin/studios/form.html", {"form": form, "studio": studio})


@staff_member_required
def studio_detail_view(request, studio_id):
    studio = get_object_or_404(Studio, pk=studio_id)
    return render(request, "admin/studios/detail.html", {
        "studio": studio,
        "upcoming_reservations": studio.reservation_set.select_related("user")
            .filter(start_datetime__gte=timezone.now(),
                    status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED])
            .order_by("start_datetime")[:8],
    })


@staff_member_required
def studio_delete_view(request, studio_id):
    studio = get_object_or_404(Studio, pk=studio_id)
    if request.method == "POST":
        name = studio.name
        studio.delete()
        messages.success(request, f"Le studio « {name} » a été supprimé.")
        return redirect("dashboard:studios_list")
    return render(request, "admin/studios/confirm_delete.html", {
        "studio": studio,
        "reservations_count": studio.reservation_set.count(),
    })
