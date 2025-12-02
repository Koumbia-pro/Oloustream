# apps/core/views.py
from django.shortcuts import render
from django.conf import settings
from apps.services_app.models import Service, Partner, Training
from apps.studio.models import Studio   # <--- AJOUT

def home_view(request):
    services = (
        Service.objects.filter(is_active=True)
        .order_by("name")[:6]
    )
    partners = (
        Partner.objects.filter(active=True)
        .order_by("name")[:10]
    )
    projects = []

    hero_video_url = settings.MEDIA_URL + "hero/hero.mp4"

    partners_count = partners.count()
    projects_count = 936
    streaming_views = 29
    countries_count = 7

    # Image formation existante
    training_image_url = None
    training = Training.objects.filter(is_active=True, image__isnull=False).first()
    if training and training.image:
        training_image_url = training.image.url

    studio_image_url = None
    material_image_url = None

    # NOUVEAU : studios pour la section “nos studios”
    studios = Studio.objects.filter(is_active=True)[:6]

    context = {
        "services": services,
        "partners": partners,
        "projects": projects,
        "hero_video_url": hero_video_url,
        "partners_count": partners_count,
        "projects_count": projects_count,
        "streaming_views": streaming_views,
        "countries_count": countries_count,
        "training_image_url": training_image_url,
        "studio_image_url": studio_image_url,
        "material_image_url": material_image_url,
        "studios": studios,   # <--- IMPORTANT
    }
    return render(request, "front/home.html", context)