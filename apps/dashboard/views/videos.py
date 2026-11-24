"""Vidéos YouTube affichées dans les réalisations (accueil et page Réalisations)."""
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.forms import VideoRealisationForm
from apps.core.models import VideoRealisation

__all__ = [
    "video_list_view", "video_create_view", "video_update_view", "video_delete_view", "video_toggle_view",
]

HOME_LIMIT = 4


@staff_member_required
def video_list_view(request):
    qs = VideoRealisation.objects.all()
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(tags__icontains=q))
    if category in VideoRealisation.Category.values:
        qs = qs.filter(category=category)

    stats = VideoRealisation.objects.aggregate(
        total=Count("id"),
        published=Count("id", filter=Q(is_published=True)),
        hidden=Count("id", filter=Q(is_published=False)),
    )
    # Vidéos réellement visibles sur l'accueil (les 4 premières publiées et cochées)
    home_ids = set(VideoRealisation.objects.filter(is_published=True, show_on_home=True)
                   .values_list("id", flat=True)[:HOME_LIMIT])
    return render(request, "admin/videos/list.html", {
        "videos": qs,
        "home_ids": home_ids,
        "stats": stats,
        "home_count": len(home_ids),
        "home_limit": HOME_LIMIT,
        "q": q,
        "selected_category": category,
        "category_choices": VideoRealisation.Category.choices,
        "is_filtered": bool(q or category),
    })


@staff_member_required
def video_create_view(request):
    initial = {"order": (VideoRealisation.objects.order_by("-order").values_list("order", flat=True).first() or 0) + 10}
    form = VideoRealisationForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        video = form.save()
        messages.success(request, f"Vidéo « {video.title} » ajoutée.")
        return redirect("dashboard:videos_list")
    return render(request, "admin/videos/form.html", {"form": form, "video": None})


@staff_member_required
def video_update_view(request, video_id):
    video = get_object_or_404(VideoRealisation, pk=video_id)
    form = VideoRealisationForm(request.POST or None, instance=video)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Vidéo mise à jour.")
        return redirect("dashboard:videos_list")
    return render(request, "admin/videos/form.html", {"form": form, "video": video})


@staff_member_required
@require_POST
def video_toggle_view(request, video_id):
    """Bascule rapide depuis la liste : publication ou affichage sur l'accueil."""
    video = get_object_or_404(VideoRealisation, pk=video_id)
    field = request.POST.get("field")
    if field in ("is_published", "show_on_home"):
        setattr(video, field, not getattr(video, field))
        video.save(update_fields=[field])
        messages.success(request, "Affichage mis à jour.")
    return redirect("dashboard:videos_list")


@staff_member_required
def video_delete_view(request, video_id):
    video = get_object_or_404(VideoRealisation, pk=video_id)
    if request.method == "POST":
        title = video.title
        video.delete()
        messages.success(request, f"Vidéo « {title} » supprimée.")
        return redirect("dashboard:videos_list")
    return render(request, "admin/videos/confirm_delete.html", {"video": video})
