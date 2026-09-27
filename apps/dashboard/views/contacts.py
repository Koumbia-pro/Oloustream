"""Demandes de contact et de devis reçues depuis le site."""
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.models import ContactRequest
from apps.core.utils import querystring_without_page

__all__ = ["contacts_list_view", "contact_detail_view", "contact_update_view", "contact_delete_view"]


@staff_member_required
def contacts_list_view(request):
    qs = ContactRequest.objects.all()
    status = request.GET.get("status", "")
    subject = request.GET.get("subject", "")
    q = request.GET.get("q", "").strip()
    if status in ContactRequest.Status.values:
        qs = qs.filter(status=status)
    if subject in ContactRequest.Subject.values:
        qs = qs.filter(subject=subject)
    if q:
        qs = qs.filter(Q(full_name__icontains=q) | Q(company__icontains=q) | Q(email__icontains=q)
                       | Q(phone__icontains=q) | Q(message__icontains=q))

    stats = ContactRequest.objects.aggregate(
        total=Count("id"),
        new=Count("id", filter=Q(status=ContactRequest.Status.NEW)),
        in_progress=Count("id", filter=Q(status=ContactRequest.Status.IN_PROGRESS)),
        done=Count("id", filter=Q(status=ContactRequest.Status.DONE)),
    )
    return render(request, "admin/contacts/list.html", {
        "page_obj": Paginator(qs, 15).get_page(request.GET.get("page")),
        "stats": stats,
        "status_choices": ContactRequest.Status.choices,
        "subject_choices": ContactRequest.Subject.choices,
        "selected_status": status,
        "selected_subject": subject,
        "q": q,
        "base_querystring": querystring_without_page(request),
    })


@staff_member_required
def contact_detail_view(request, pk):
    contact = get_object_or_404(ContactRequest, pk=pk)
    return render(request, "admin/contacts/detail.html", {
        "contact": contact,
        "status_choices": ContactRequest.Status.choices,
    })


@staff_member_required
@require_POST
def contact_update_view(request, pk):
    contact = get_object_or_404(ContactRequest, pk=pk)
    status = request.POST.get("status")
    if status in ContactRequest.Status.values:
        contact.status = status
    contact.internal_notes = request.POST.get("internal_notes", contact.internal_notes)
    contact.save(update_fields=["status", "internal_notes"])
    messages.success(request, "Demande mise à jour.")
    return redirect("dashboard:contact_detail", pk=pk)


@staff_member_required
@require_POST
def contact_delete_view(request, pk):
    contact = get_object_or_404(ContactRequest, pk=pk)
    contact.delete()
    messages.success(request, "Demande supprimée.")
    return redirect("dashboard:contacts_list")
