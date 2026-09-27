"""Partenaires institutionnels / clients affichés sur le site (logos)."""
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.core.utils import excel_response, querystring_without_page, yes_no
from apps.services_app.forms import PartnerForm
from apps.services_app.models import Partner

__all__ = [
    "partner_list_view", "partner_export_excel_view", "partner_detail_view", "partner_create_view",
    "partner_update_view", "partner_delete_view",
]


def _filtered_partners(request):
    qs = Partner.objects.order_by("name")
    filters = {"q": request.GET.get("q", "").strip(), "active": request.GET.get("active", "")}
    if filters["q"]:
        q = filters["q"]
        qs = qs.filter(Q(name__icontains=q) | Q(website__icontains=q) | Q(contact_name__icontains=q))
    if filters["active"] == "yes":
        qs = qs.filter(active=True)
    elif filters["active"] == "no":
        qs = qs.filter(active=False)
    return qs, filters


@staff_member_required
def partner_list_view(request):
    qs, filters = _filtered_partners(request)
    stats = qs.aggregate(total=Count("id"), n_active=Count("id", filter=Q(active=True)),
                         n_inactive=Count("id", filter=Q(active=False)))
    return render(request, "admin/partners/list.html", {
        "page_obj": Paginator(qs, 12).get_page(request.GET.get("page")),
        "q": filters["q"],
        "selected_active": filters["active"],
        "base_querystring": querystring_without_page(request),
        "total_count": stats["total"], "active_count": stats["n_active"], "inactive_count": stats["n_inactive"],
    })


@staff_member_required
def partner_export_excel_view(request):
    qs, _ = _filtered_partners(request)
    rows = [[p.id, p.name, p.get_partnership_type_display(), p.contact_name, p.contact_email,
             p.contact_phone, p.website, yes_no(p.active)] for p in qs]
    return excel_response(
        "partenaires", "Partenaires",
        ["ID", "Nom", "Type", "Contact", "Email", "Téléphone", "Site web", "Actif"],
        rows, [6, 26, 18, 20, 26, 16, 30, 8],
    )


@staff_member_required
def partner_detail_view(request, partner_id):
    return render(request, "admin/partners/detail.html", {"partner": get_object_or_404(Partner, pk=partner_id)})


@staff_member_required
def partner_create_view(request):
    form = PartnerForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        partner = form.save()
        messages.success(request, f"Partenaire « {partner.name} » créé avec succès.")
        return redirect("dashboard:partners_detail", partner_id=partner.pk)
    return render(request, "admin/partners/form.html", {"form": form, "partner": None})


@staff_member_required
def partner_update_view(request, partner_id):
    partner = get_object_or_404(Partner, pk=partner_id)
    form = PartnerForm(request.POST or None, request.FILES or None, instance=partner)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Partenaire mis à jour avec succès.")
        return redirect("dashboard:partners_detail", partner_id=partner.pk)
    return render(request, "admin/partners/form.html", {"form": form, "partner": partner})


@staff_member_required
def partner_delete_view(request, partner_id):
    partner = get_object_or_404(Partner, pk=partner_id)
    if request.method == "POST":
        name = partner.name
        partner.delete()
        messages.success(request, f"Partenaire « {name} » supprimé.")
        return redirect("dashboard:partners_list")
    return render(request, "admin/partners/confirm_delete.html", {"partner": partner})
