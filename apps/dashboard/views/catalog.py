"""Catalogue : services, offres promotionnelles et formations."""
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.core.utils import excel_response, fmt_date, fmt_datetime, parse_int, querystring_without_page, yes_no
from apps.services_app.forms import OfferForm, ServiceForm, TrainingForm
from apps.services_app.models import (
    Offer, Service, ServiceCategory, ServiceTypeChoices, Training, TrainingCategory,
    TrainingLevelChoices, TrainingModeChoices,
)

__all__ = [
    "service_list_view", "service_detail_view", "service_export_excel_view", "service_create_view",
    "service_update_view", "service_delete_view",
    "offer_list_view", "offer_export_excel_view", "offer_detail_view", "offer_create_view",
    "offer_update_view", "offer_delete_view",
    "training_list_view", "training_export_excel_view", "training_create_view", "training_update_view",
    "training_delete_view", "training_detail_view",
]


def _active_filter(qs, value, field="is_active"):
    if value == "yes":
        return qs.filter(**{field: True})
    if value == "no":
        return qs.filter(**{field: False})
    return qs


def _period_label(start, end, today, labels=("En cours", "À venir", "Expirée"), empty="Non définie"):
    if not (start and end):
        return empty
    if start <= today <= end:
        return labels[0]
    if start > today:
        return labels[1]
    return labels[2]


# ==================== SERVICES ====================

def _filtered_services(request):
    qs = Service.objects.select_related("category").order_by("name")
    filters = {
        "q": request.GET.get("q", "").strip(),
        "category": request.GET.get("category", ""),
        "service_type": request.GET.get("service_type", ""),
        "active": request.GET.get("active", ""),
    }
    if filters["q"]:
        q = filters["q"]
        qs = qs.filter(Q(name__icontains=q) | Q(short_description__icontains=q)
                       | Q(description__icontains=q) | Q(category__name__icontains=q))
    category_id = parse_int(filters["category"])
    if category_id:
        qs = qs.filter(category_id=category_id)
    if filters["service_type"] in ServiceTypeChoices.values:
        qs = qs.filter(service_type=filters["service_type"])
    return _active_filter(qs, filters["active"]), filters


@staff_member_required
def service_list_view(request):
    qs, filters = _filtered_services(request)
    stats = qs.aggregate(total=Count("id"), active=Count("id", filter=Q(is_active=True)),
                         inactive=Count("id", filter=Q(is_active=False)))
    return render(request, "admin/services/list.html", {
        "page_obj": Paginator(qs, 12).get_page(request.GET.get("page")),
        "q": filters["q"],
        "selected_category": filters["category"],
        "selected_service_type": filters["service_type"],
        "selected_active": filters["active"],
        "categories": ServiceCategory.objects.order_by("name"),
        "service_type_choices": ServiceTypeChoices.choices,
        "base_querystring": querystring_without_page(request),
        "total_count": stats["total"], "active_count": stats["active"], "inactive_count": stats["inactive"],
    })


@staff_member_required
def service_detail_view(request, service_id):
    service = get_object_or_404(Service.objects.select_related("category"), pk=service_id)
    return render(request, "admin/services/detail.html", {
        "service": service,
        "offers": service.offers.order_by("-start_date")[:5],
        "reservations_count": service.reservations.count(),
    })


@staff_member_required
def service_export_excel_view(request):
    qs, _ = _filtered_services(request)
    rows = [[
        s.id, s.name, s.category.name if s.category else "", s.get_service_type_display(),
        float(s.base_price), s.duration_min_minutes or "", s.duration_max_minutes or "",
        s.get_location_type_display(), s.get_difficulty_level_display(), yes_no(s.requires_studio),
        yes_no(s.requires_equipment_rental), yes_no(s.is_active), fmt_datetime(s.created_at),
    ] for s in qs]
    return excel_response(
        "services", "Services",
        ["ID", "Nom", "Catégorie", "Type", "Prix de base", "Durée min (min)", "Durée max (min)",
         "Lieu", "Complexité", "Studio requis", "Location matériel", "Actif", "Créé le"],
        rows, [6, 26, 20, 18, 14, 12, 12, 18, 16, 12, 16, 8, 17],
    )


@staff_member_required
def service_create_view(request):
    form = ServiceForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        service = form.save()
        messages.success(request, f"Service « {service.name} » créé avec succès.")
        return redirect("dashboard:services_detail", service_id=service.pk)
    return render(request, "admin/services/form.html", {"form": form, "service": None})


@staff_member_required
def service_update_view(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    form = ServiceForm(request.POST or None, request.FILES or None, instance=service)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Service mis à jour avec succès.")
        return redirect("dashboard:services_detail", service_id=service.pk)
    return render(request, "admin/services/form.html", {"form": form, "service": service})


@staff_member_required
def service_delete_view(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    if request.method == "POST":
        name = service.name
        service.delete()
        messages.success(request, f"Service « {name} » supprimé.")
        return redirect("dashboard:services_list")
    return render(request, "admin/services/confirm_delete.html", {
        "service": service,
        "offers_count": service.offers.count(),
    })


# ==================== OFFRES ====================

def _filtered_offers(request):
    qs = Offer.objects.select_related("service").order_by("-start_date")
    today = timezone.localdate()
    filters = {
        "q": request.GET.get("q", "").strip(),
        "service": request.GET.get("service", ""),
        "active": request.GET.get("active", ""),
        "period": request.GET.get("period", ""),
    }
    if filters["q"]:
        q = filters["q"]
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(service__name__icontains=q))
    service_id = parse_int(filters["service"])
    if service_id:
        qs = qs.filter(service_id=service_id)
    qs = _active_filter(qs, filters["active"])
    if filters["period"] == "current":
        qs = qs.filter(start_date__lte=today, end_date__gte=today)
    elif filters["period"] == "upcoming":
        qs = qs.filter(start_date__gt=today)
    elif filters["period"] == "expired":
        qs = qs.filter(end_date__lt=today)
    return qs, filters


@staff_member_required
def offer_list_view(request):
    qs, filters = _filtered_offers(request)
    today = timezone.localdate()
    stats = qs.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        inactive=Count("id", filter=Q(is_active=False)),
        current=Count("id", filter=Q(is_active=True, start_date__lte=today, end_date__gte=today)),
        upcoming=Count("id", filter=Q(start_date__gt=today)),
        expired=Count("id", filter=Q(end_date__lt=today)),
    )
    return render(request, "admin/offers/list.html", {
        "page_obj": Paginator(qs, 12).get_page(request.GET.get("page")),
        "q": filters["q"],
        "selected_service": filters["service"],
        "selected_active": filters["active"],
        "selected_period": filters["period"],
        "services": Service.objects.filter(is_active=True).order_by("name"),
        "base_querystring": querystring_without_page(request),
        "today": today,
        **{f"{key}_count": value for key, value in stats.items()},
    })


@staff_member_required
def offer_export_excel_view(request):
    qs, _ = _filtered_offers(request)
    today = timezone.localdate()
    rows = [[
        o.id, o.title, o.service.name if o.service else "", o.discount_percent,
        fmt_date(o.start_date), fmt_date(o.end_date), _period_label(o.start_date, o.end_date, today, empty=""),
        yes_no(o.is_active), (o.description or "")[:200],
    ] for o in qs]
    return excel_response(
        "offres", "Offres",
        ["ID", "Titre", "Service", "Réduction (%)", "Début", "Fin", "Période", "Active", "Description"],
        rows, [6, 26, 24, 12, 12, 12, 12, 8, 50],
    )


@staff_member_required
def offer_detail_view(request, offer_id):
    offer = get_object_or_404(Offer.objects.select_related("service"), pk=offer_id)
    return render(request, "admin/offers/detail.html", {
        "offer": offer,
        "period_label": _period_label(offer.start_date, offer.end_date, timezone.localdate()),
        "applications": offer.applications.select_related("user").order_by("-created_at"),
    })


@staff_member_required
def offer_create_view(request):
    form = OfferForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        offer = form.save()
        messages.success(request, f"Offre « {offer.title} » créée avec succès.")
        return redirect("dashboard:offers_detail", offer_id=offer.pk)
    return render(request, "admin/offers/form.html", {"form": form, "offer": None})


@staff_member_required
def offer_update_view(request, offer_id):
    offer = get_object_or_404(Offer, pk=offer_id)
    form = OfferForm(request.POST or None, instance=offer)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Offre mise à jour avec succès.")
        return redirect("dashboard:offers_detail", offer_id=offer.pk)
    return render(request, "admin/offers/form.html", {"form": form, "offer": offer})


@staff_member_required
def offer_delete_view(request, offer_id):
    offer = get_object_or_404(Offer, pk=offer_id)
    if request.method == "POST":
        title = offer.title
        offer.delete()
        messages.success(request, f"Offre « {title} » supprimée.")
        return redirect("dashboard:offers_list")
    return render(request, "admin/offers/confirm_delete.html", {"offer": offer})


# ==================== FORMATIONS ====================

def _filtered_trainings(request):
    qs = Training.objects.select_related("category").order_by("title")
    filters = {
        "q": request.GET.get("q", "").strip(),
        "category": request.GET.get("category", ""),
        "level": request.GET.get("level", ""),
        "mode": request.GET.get("mode", ""),
        "active": request.GET.get("active", ""),
    }
    if filters["q"]:
        q = filters["q"]
        qs = qs.filter(Q(title__icontains=q) | Q(short_description__icontains=q)
                       | Q(description__icontains=q) | Q(category__name__icontains=q))
    category_id = parse_int(filters["category"])
    if category_id:
        qs = qs.filter(category_id=category_id)
    if filters["level"] in TrainingLevelChoices.values:
        qs = qs.filter(level=filters["level"])
    if filters["mode"] in TrainingModeChoices.values:
        qs = qs.filter(mode=filters["mode"])
    return _active_filter(qs, filters["active"]), filters


@staff_member_required
def training_list_view(request):
    qs, filters = _filtered_trainings(request)
    stats = qs.aggregate(total=Count("id"), active=Count("id", filter=Q(is_active=True)),
                         inactive=Count("id", filter=Q(is_active=False)))
    return render(request, "admin/trainings/list.html", {
        "page_obj": Paginator(qs.annotate(enrollments_count=Count("enrollments")), 12).get_page(request.GET.get("page")),
        "q": filters["q"],
        "selected_category": filters["category"],
        "selected_level": filters["level"],
        "selected_mode": filters["mode"],
        "selected_active": filters["active"],
        "categories": TrainingCategory.objects.order_by("name"),
        "levels": TrainingLevelChoices.choices,
        "modes": TrainingModeChoices.choices,
        "base_querystring": querystring_without_page(request),
        "total_count": stats["total"], "active_count": stats["active"], "inactive_count": stats["inactive"],
    })


@staff_member_required
def training_export_excel_view(request):
    qs, _ = _filtered_trainings(request)
    rows = [[
        t.id, t.title, t.category.name if t.category else "", t.get_level_display(), t.get_mode_display(),
        t.location, t.duration_hours or "", float(t.price) if t.price is not None else None,
        yes_no(t.certification), yes_no(t.is_active), fmt_date(t.start_date), fmt_date(t.end_date),
    ] for t in qs]
    return excel_response(
        "formations", "Formations",
        ["ID", "Titre", "Catégorie", "Niveau", "Mode", "Lieu", "Durée (h)", "Prix (FCFA)",
         "Certification", "Active", "Début", "Fin"],
        rows, [6, 28, 20, 16, 16, 20, 10, 14, 12, 8, 12, 12],
    )


@staff_member_required
def training_detail_view(request, training_id):
    training = get_object_or_404(Training.objects.select_related("category"), pk=training_id)
    return render(request, "admin/trainings/detail.html", {
        "training": training,
        "period_label": _period_label(training.start_date, training.end_date, timezone.localdate(),
                                      labels=("En cours", "À venir", "Terminée"), empty="Non planifiée"),
        "enrollments": training.enrollments.select_related("user").order_by("-created_at"),
    })


@staff_member_required
def training_create_view(request):
    form = TrainingForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        training = form.save()
        messages.success(request, f"Formation « {training.title} » créée avec succès.")
        return redirect("dashboard:trainings_detail", training_id=training.pk)
    return render(request, "admin/trainings/form.html", {"form": form, "training": None})


@staff_member_required
def training_update_view(request, training_id):
    training = get_object_or_404(Training, pk=training_id)
    form = TrainingForm(request.POST or None, request.FILES or None, instance=training)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Formation mise à jour avec succès.")
        return redirect("dashboard:trainings_detail", training_id=training.pk)
    return render(request, "admin/trainings/form.html", {"form": form, "training": training})


@staff_member_required
def training_delete_view(request, training_id):
    training = get_object_or_404(Training, pk=training_id)
    if request.method == "POST":
        title = training.title
        training.delete()
        messages.success(request, f"Formation « {title} » supprimée.")
        return redirect("dashboard:trainings_list")
    return render(request, "admin/trainings/confirm_delete.html", {"training": training})
