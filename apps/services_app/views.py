from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.core.utils import send_safely

from .forms import JobApplicationForm, JobApplicationStatusForm, JobOfferForm, OfferApplicationForm
from .models import (
    JobApplication, JobOffer, JobOfferStatusChoices, JobOfferTypeChoices, Offer, OfferApplication,
    Training, TrainingEnrollment,
)


# ---------- FORMATIONS (UTILISATEUR) ----------

def user_training_list_view(request):
    trainings = Training.objects.filter(is_active=True).select_related("category").order_by("start_date", "title")

    user_training_ids = set()
    if request.user.is_authenticated:
        user_training_ids = set(
            TrainingEnrollment.objects.filter(user=request.user).values_list('training_id', flat=True)
        )

    return render(request, "user/trainings/list.html", {
        "trainings": trainings,
        "user_training_ids": user_training_ids,
    })


@login_required
@require_POST
def user_training_enroll_view(request, training_id):
    training = get_object_or_404(Training, pk=training_id, is_active=True)

    if training.max_seats and training.enrollments.count() >= training.max_seats:
        messages.error(request, "Désolé, cette formation est complète.")
        return redirect('services_app:user_trainings_list')

    try:
        _, created = TrainingEnrollment.objects.get_or_create(
            user=request.user, training=training, defaults={"status": "PENDING"},
        )
    except IntegrityError:
        created = False

    if created:
        messages.success(request, f"Votre inscription à « {training.title} » est enregistrée. "
                                  "Notre équipe vous contactera pour la confirmer.")
    else:
        messages.info(request, "Vous êtes déjà inscrit à cette formation.")
    return redirect('services_app:user_trainings_list')


# ---------- OFFRES (UTILISATEUR) ----------

def user_offer_list_view(request):
    today = timezone.localdate()
    offers = Offer.objects.filter(is_active=True, end_date__gte=today).select_related("service").order_by("end_date")

    user_offer_ids = set()
    if request.user.is_authenticated:
        user_offer_ids = set(
            OfferApplication.objects.filter(user=request.user).values_list('offer_id', flat=True)
        )

    return render(request, "user/offers/list.html", {
        "offers": offers,
        "user_offer_ids": user_offer_ids,
    })


@login_required
def user_offer_apply_view(request, offer_id):
    offer = get_object_or_404(Offer, pk=offer_id, is_active=True)

    if OfferApplication.objects.filter(user=request.user, offer=offer).exists():
        messages.info(request, "Vous avez déjà postulé à cette offre.")
        return redirect('services_app:user_offers_list')

    form = OfferApplicationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        application = form.save(commit=False)
        application.user = request.user
        application.offer = offer
        try:
            application.save()
        except IntegrityError:
            messages.info(request, "Vous avez déjà postulé à cette offre.")
        else:
            messages.success(request, "Votre demande a été envoyée. Nous revenons vers vous rapidement.")
        return redirect('services_app:user_offers_list')

    return render(request, "user/offers/apply.html", {"form": form, "offer": offer})


# ------------------ JOBS (USER) ------------------

def user_jobs_list_view(request):
    offers = JobOffer.objects.filter(status=JobOfferStatusChoices.PUBLISHED).order_by("-created_at")

    offer_type = request.GET.get("type", "")
    if offer_type in JobOfferTypeChoices.values:
        offers = offers.filter(offer_type=offer_type)

    q = request.GET.get("q", "").strip()
    if q:
        offers = offers.filter(
            Q(title__icontains=q) | Q(summary__icontains=q) | Q(location__icontains=q) | Q(department__icontains=q)
        )

    return render(request, "user/jobs/list.html", {
        "offers": offers,
        "q": q,
        "current_type": offer_type,
        "type_choices": JobOfferTypeChoices.choices,
    })


def user_jobs_detail_view(request, slug):
    offer = get_object_or_404(JobOffer, slug=slug, status=JobOfferStatusChoices.PUBLISHED)
    already_applied = (
        request.user.is_authenticated
        and JobApplication.objects.filter(user=request.user, offer=offer).exists()
    )
    return render(request, "user/jobs/detail.html", {"offer": offer, "already_applied": already_applied})


@login_required
def user_jobs_apply_view(request, slug):
    offer = get_object_or_404(JobOffer, slug=slug, status=JobOfferStatusChoices.PUBLISHED)

    if not offer.is_open:
        messages.error(request, "Cette offre est fermée.")
        return redirect("services_app:user_jobs_detail", slug=offer.slug)

    if JobApplication.objects.filter(user=request.user, offer=offer).exists():
        messages.info(request, "Vous avez déjà postulé à cette offre.")
        return redirect("services_app:user_jobs_detail", slug=offer.slug)

    initial = {
        "email": request.user.email or "",
        "full_name": (request.user.get_full_name() or request.user.username).strip(),
        "phone": getattr(request.user, "phone", ""),
    }

    form = JobApplicationForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        application = form.save(commit=False)
        application.user = request.user
        application.offer = offer
        try:
            application.save()
        except IntegrityError:
            messages.info(request, "Vous avez déjà postulé à cette offre.")
            return redirect("services_app:user_jobs_detail", slug=offer.slug)

        from apps.notifications.emailing import send_job_application_confirmation
        if send_safely(send_job_application_confirmation, application):
            messages.success(request, "Votre candidature a bien été envoyée. Un email de confirmation vous a été adressé.")
        else:
            messages.success(request, "Votre candidature a bien été enregistrée.")
        return redirect("services_app:user_jobs_detail", slug=offer.slug)

    return render(request, "user/jobs/apply.html", {"offer": offer, "form": form})


# ------------------ JOBS (ADMIN) ------------------

@staff_member_required
def admin_jobs_list_view(request):
    offers = JobOffer.objects.annotate(
        applications_count=Count("applications"),
        pending_count=Count("applications", filter=Q(applications__status="PENDING")),
    ).order_by("-created_at")
    status = request.GET.get("status", "")
    if status in JobOfferStatusChoices.values:
        offers = offers.filter(status=status)
    return render(request, "admin/jobs/list.html", {
        "offers": offers,
        "status_choices": JobOfferStatusChoices.choices,
        "current_status": status,
    })


@staff_member_required
def admin_jobs_create_view(request):
    form = JobOfferForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        offer = form.save()
        messages.success(request, "Offre créée.")
        return redirect("services_app:admin_jobs_detail", pk=offer.pk)
    return render(request, "admin/jobs/form.html", {"form": form})


@staff_member_required
def admin_jobs_edit_view(request, pk):
    offer = get_object_or_404(JobOffer, pk=pk)
    form = JobOfferForm(request.POST or None, request.FILES or None, instance=offer)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Offre mise à jour.")
        return redirect("services_app:admin_jobs_detail", pk=offer.pk)
    return render(request, "admin/jobs/form.html", {"form": form, "offer": offer})


@staff_member_required
def admin_jobs_applications_view(request, pk):
    offer = get_object_or_404(JobOffer, pk=pk)
    applications = offer.applications.select_related("user").order_by("-created_at")
    return render(request, "admin/jobs/applications.html", {"offer": offer, "applications": applications})


@staff_member_required
def admin_job_application_update_view(request, pk):
    application = get_object_or_404(JobApplication.objects.select_related("offer"), pk=pk)
    form = JobApplicationStatusForm(request.POST or None, instance=application)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Statut mis à jour.")
        return redirect("services_app:admin_jobs_applications", pk=application.offer_id)
    return render(request, "admin/jobs/application_update.html", {"application": application, "form": form})


@staff_member_required
def admin_jobs_detail_view(request, pk):
    offer = get_object_or_404(JobOffer, pk=pk)
    return render(request, "admin/jobs/detail.html", {
        "offer": offer,
        "applications": offer.applications.order_by("-created_at")[:5],
        "applications_count": offer.applications.count(),
    })


@staff_member_required
def admin_jobs_delete_view(request, pk):
    offer = get_object_or_404(JobOffer, pk=pk)
    if request.method == "POST":
        offer.delete()
        messages.success(request, "Offre supprimée.")
        return redirect("services_app:admin_jobs_list")
    return render(request, "admin/jobs/confirm_delete.html", {"offer": offer})
