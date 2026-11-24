"""Témoignages clients affichés sur l'accueil du site."""
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.forms import TestimonialForm
from apps.core.models import Testimonial

__all__ = [
    "testimonial_list_view", "testimonial_create_view", "testimonial_update_view",
    "testimonial_toggle_view", "testimonial_delete_view",
]

HOME_LIMIT = 6


@staff_member_required
def testimonial_list_view(request):
    stats = Testimonial.objects.aggregate(
        total=Count("id"),
        published=Count("id", filter=Q(is_published=True)),
        hidden=Count("id", filter=Q(is_published=False)),
    )
    home_ids = set(Testimonial.objects.filter(is_published=True).values_list("id", flat=True)[:HOME_LIMIT])
    return render(request, "admin/testimonials/list.html", {
        "testimonials": Testimonial.objects.all(),
        "stats": stats,
        "home_ids": home_ids,
        "home_limit": HOME_LIMIT,
    })


@staff_member_required
def testimonial_create_view(request):
    initial = {"order": (Testimonial.objects.order_by("-order").values_list("order", flat=True).first() or 0) + 10}
    form = TestimonialForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Témoignage ajouté.")
        return redirect("dashboard:testimonials_list")
    return render(request, "admin/testimonials/form.html", {"form": form, "testimonial": None})


@staff_member_required
def testimonial_update_view(request, testimonial_id):
    testimonial = get_object_or_404(Testimonial, pk=testimonial_id)
    form = TestimonialForm(request.POST or None, request.FILES or None, instance=testimonial)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Témoignage mis à jour.")
        return redirect("dashboard:testimonials_list")
    return render(request, "admin/testimonials/form.html", {"form": form, "testimonial": testimonial})


@staff_member_required
@require_POST
def testimonial_toggle_view(request, testimonial_id):
    testimonial = get_object_or_404(Testimonial, pk=testimonial_id)
    testimonial.is_published = not testimonial.is_published
    testimonial.save(update_fields=["is_published"])
    messages.success(request, "Témoignage publié." if testimonial.is_published else "Témoignage masqué.")
    return redirect("dashboard:testimonials_list")


@staff_member_required
def testimonial_delete_view(request, testimonial_id):
    testimonial = get_object_or_404(Testimonial, pk=testimonial_id)
    if request.method == "POST":
        testimonial.delete()
        messages.success(request, "Témoignage supprimé.")
        return redirect("dashboard:testimonials_list")
    return render(request, "admin/testimonials/confirm_delete.html", {"testimonial": testimonial})
