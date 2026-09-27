from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from apps.core.utils import excel_response, fmt_date, parse_int, querystring_without_page, yes_no
from apps.studio.choices import EquipmentStatus
from apps.studio.forms import EquipmentForm
from apps.studio.models import Equipment, EquipmentCategory

__all__ = [
    "equipment_list_view", "equipment_export_excel_view", "equipment_detail_view",
    "equipment_create_view", "equipment_update_view", "equipment_delete_view",
]


def _filtered_equipments(request):
    qs = Equipment.objects.select_related("category", "current_user").order_by("name")
    filters = {
        "q": request.GET.get("q", "").strip(),
        "category": request.GET.get("category", ""),
        "status": request.GET.get("status", ""),
        "rental": request.GET.get("rental", ""),
    }
    if filters["q"]:
        q = filters["q"]
        qs = qs.filter(
            Q(name__icontains=q) | Q(brand__icontains=q) | Q(model__icontains=q)
            | Q(serial_number__icontains=q) | Q(location__icontains=q) | Q(category__name__icontains=q)
        )
    category_id = parse_int(filters["category"])
    if category_id:
        qs = qs.filter(category_id=category_id)
    if filters["status"] in EquipmentStatus.values:
        qs = qs.filter(status=filters["status"])
    if filters["rental"] == "yes":
        qs = qs.filter(is_available_for_rent=True)
    elif filters["rental"] == "no":
        qs = qs.filter(is_available_for_rent=False)
    return qs, filters


@staff_member_required
def equipment_list_view(request):
    qs, filters = _filtered_equipments(request)
    stats = qs.aggregate(
        total=Count("id"),
        available=Count("id", filter=Q(status=EquipmentStatus.AVAILABLE)),
        in_use=Count("id", filter=Q(status=EquipmentStatus.IN_USE)),
        maintenance=Count("id", filter=Q(status=EquipmentStatus.MAINTENANCE)),
        out_of_service=Count("id", filter=Q(status=EquipmentStatus.OUT_OF_SERVICE)),
        retired=Count("id", filter=Q(status=EquipmentStatus.RETIRED)),
        value=Sum("purchase_price"),
    )
    return render(request, "admin/equipments/list.html", {
        "page_obj": Paginator(qs, 12).get_page(request.GET.get("page")),
        "q": filters["q"],
        "selected_category": filters["category"],
        "selected_status": filters["status"],
        "selected_rental": filters["rental"],
        "categories": EquipmentCategory.objects.order_by("name"),
        "status_choices": EquipmentStatus.choices,
        "base_querystring": querystring_without_page(request),
        "total_count": stats["total"],
        "available_count": stats["available"],
        "in_use_count": stats["in_use"],
        "maintenance_count": stats["maintenance"],
        "out_of_service_count": stats["out_of_service"],
        "retired_count": stats["retired"],
        "total_value": stats["value"] or 0,
    })


@staff_member_required
def equipment_export_excel_view(request):
    qs, _ = _filtered_equipments(request)
    rows = [[
        e.id, e.name, e.category.name if e.category else "", e.brand, e.model, e.serial_number or "",
        e.get_status_display(), yes_no(e.is_available_for_rent), e.location,
        e.current_user.get_full_name() if e.current_user else "",
        fmt_date(e.purchase_date),
        float(e.purchase_price) if e.purchase_price is not None else None,
        e.age_years if e.age_years is not None else "",
        fmt_date(e.last_maintenance_date), fmt_date(e.next_maintenance_date),
    ] for e in qs]
    return excel_response(
        "equipements", "Équipements",
        ["ID", "Nom", "Catégorie", "Marque", "Modèle", "N° de série", "Statut", "Location",
         "Emplacement", "Utilisateur actuel", "Date d'achat", "Prix d'achat", "Âge (ans)",
         "Dernière maintenance", "Prochaine maintenance"],
        rows, [6, 26, 18, 16, 16, 18, 16, 10, 18, 22, 14, 14, 10, 18, 18],
    )


@staff_member_required
def equipment_detail_view(request, equipment_id):
    equipment = get_object_or_404(Equipment.objects.select_related("category", "current_user"), pk=equipment_id)
    return render(request, "admin/equipments/detail.html", {
        "equipment": equipment,
        "recent_reservations": equipment.reservations.select_related("user").order_by("-start_datetime")[:5],
    })


@staff_member_required
def equipment_create_view(request):
    form = EquipmentForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        equipment = form.save()
        messages.success(request, f"Équipement « {equipment.name} » créé avec succès.")
        return redirect("dashboard:equipments_detail", equipment_id=equipment.pk)
    return render(request, "admin/equipments/form.html", {"form": form, "equipment": None})


@staff_member_required
def equipment_update_view(request, equipment_id):
    equipment = get_object_or_404(Equipment, pk=equipment_id)
    form = EquipmentForm(request.POST or None, request.FILES or None, instance=equipment)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Équipement mis à jour avec succès.")
        return redirect("dashboard:equipments_detail", equipment_id=equipment.pk)
    return render(request, "admin/equipments/form.html", {"form": form, "equipment": equipment})


@staff_member_required
def equipment_delete_view(request, equipment_id):
    equipment = get_object_or_404(Equipment, pk=equipment_id)
    if request.method == "POST":
        name = equipment.name
        equipment.delete()
        messages.success(request, f"Équipement « {name} » supprimé.")
        return redirect("dashboard:equipments_list")
    return render(request, "admin/equipments/confirm_delete.html", {"equipment": equipment})
