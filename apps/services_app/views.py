from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Service, Offer, Training, TrainingEnrollment, OfferApplication
from .forms import OfferApplicationForm

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from .models import JobOffer, JobApplication, JobOfferStatusChoices
from .forms import JobOfferForm, JobApplicationForm

from django.core.mail import send_mail
from django.conf import settings
from .forms import JobApplicationStatusForm
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


# ---------- FORMATIONS (UTILISATEUR) ----------

def user_training_list_view(request):
    trainings = Training.objects.filter(is_active=True)

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
def user_training_enroll_view(request, training_id):
    training = get_object_or_404(Training, pk=training_id, is_active=True)

    if TrainingEnrollment.objects.filter(user=request.user, training=training).exists():
        messages.info(request, "Vous êtes déjà inscrit à cette formation.")
        return redirect('services_app:user_trainings_list')

    TrainingEnrollment.objects.create(
        user=request.user,
        training=training,
        status='PENDING',
    )
    messages.success(request, "Votre inscription à la formation a été enregistrée.")
    return redirect('services_app:user_trainings_list')


# ---------- OFFRES (UTILISATEUR) ----------

def user_offer_list_view(request):
    offers = Offer.objects.filter(is_active=True)

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

    if request.method == "POST":
        form = OfferApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.offer = offer
            application.save()
            messages.success(request, "Votre candidature a été envoyée.")
            return redirect('services_app:user_offers_list')
    else:
        form = OfferApplicationForm()

    return render(request, "user/offers/apply.html", {
        "form": form,
        "offer": offer,
    })







# ------------------ JOBS (USER) ------------------

def user_jobs_list_view(request):
    offers = JobOffer.objects.filter(status=JobOfferStatusChoices.PUBLISHED)

    t = request.GET.get("type")
    if t:
        offers = offers.filter(offer_type=t)

    q = request.GET.get("q")
    if q:
        offers = offers.filter(
            Q(title__icontains=q) |
            Q(summary__icontains=q) |
            Q(location__icontains=q) |
            Q(department__icontains=q)
        )

    return render(request, "user/jobs/list.html", {"offers": offers})


def user_jobs_detail_view(request, slug):
    offer = get_object_or_404(JobOffer, slug=slug, status=JobOfferStatusChoices.PUBLISHED)
    return render(request, "user/jobs/detail.html", {"offer": offer})


# @login_required
# def user_jobs_apply_view(request, slug):
#     offer = get_object_or_404(JobOffer, slug=slug, status=JobOfferStatusChoices.PUBLISHED)

#     if not offer.is_open:
#         messages.error(request, "Cette offre est fermée.")
#         return redirect("services_app:user_jobs_detail", slug=offer.slug)

#     if JobApplication.objects.filter(user=request.user, offer=offer).exists():
#         messages.info(request, "Vous avez déjà postulé à cette offre.")
#         return redirect("services_app:user_jobs_detail", slug=offer.slug)

#     initial = {
#         "email": getattr(request.user, "email", "") or "",
#         "full_name": (request.user.get_full_name() or request.user.username).strip(),
#     }

#     if request.method == "POST":
#         form = JobApplicationForm(request.POST, request.FILES)
#         if form.is_valid():
#             app = form.save(commit=False)
#             app.user = request.user
#             app.offer = offer
#             app.save()

#             subject = "Confirmation de candidature - Oloustream"
#             to_email = app.email

#             text_body = (
#                 f"Bonjour {app.full_name},\n\n"
#                 f"Nous confirmons la réception de votre candidature pour : {offer.title}.\n"
#                 f"Notre équipe reviendra vers vous si votre profil correspond.\n\n"
#                 f"Merci,\nOloustream\n"
#                 f"www.oloustream.com"
#             )

#             # (optionnel) version HTML via template
#             # html_body = render_to_string("emails/job_application_confirmation.html", {
#             #     "full_name": app.full_name,
#             #     "offer": offer,
#             # })

#             msg = EmailMultiAlternatives(
#                 subject=subject,
#                 body=text_body,
#                 from_email=settings.DEFAULT_FROM_EMAIL,
#                 to=[to_email],
#             )
#             # msg.attach_alternative(html_body, "text/html")
#             msg.send(fail_silently=False)
#     else:
#         form = JobApplicationForm(initial=initial)

#     return render(request, "user/jobs/apply.html", {"offer": offer, "form": form})


from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

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
        "email": getattr(request.user, "email", "") or "",
        "full_name": (request.user.get_full_name() or request.user.username).strip(),
    }

    if request.method == "POST":
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.user = request.user
            app.offer = offer
            app.save()

            subject = "Confirmation de candidature - Oloustream"
            to_email = app.email

            text_body = (
                f"Bonjour {app.full_name},\n\n"
                f"Nous confirmons la réception de votre candidature pour : {offer.title}.\n"
                f"Notre équipe reviendra vers vous si votre profil correspond.\n\n"
                f"Merci,\nOloustream\n"
                f"www.oloustream.com"
            )

            try:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[to_email],
                )
                # Si tu veux envoyer une version HTML, décommente les lignes suivantes :
                # html_body = render_to_string("emails/job_application_confirmation.html", {
                #     "full_name": app.full_name,
                #     "offer": offer,
                # })
                # msg.attach_alternative(html_body, "text/html")
                msg.send(fail_silently=False)
                messages.success(request, "Votre candidature a bien été envoyée. Un email de confirmation vous a été adressé.")
            except Exception as e:
                messages.warning(request, "Votre candidature a été enregistrée, mais une erreur est survenue lors de l'envoi de l'email de confirmation.")

            return redirect("services_app:user_jobs_detail", slug=offer.slug)
    else:
        form = JobApplicationForm(initial=initial)

    return render(request, "user/jobs/apply.html", {"offer": offer, "form": form})

# ------------------ JOBS (ADMIN) ------------------

@staff_member_required
def admin_jobs_list_view(request):
    offers = JobOffer.objects.all()
    return render(request, "admin/jobs/list.html", {"offers": offers})


@staff_member_required
def admin_jobs_create_view(request):
    if request.method == "POST":
        form = JobOfferForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Offre créée.")
            return redirect("services_app:admin_jobs_list")
    else:
        form = JobOfferForm()
    return render(request, "admin/jobs/form.html", {"form": form})


@staff_member_required
def admin_jobs_edit_view(request, pk):
    offer = get_object_or_404(JobOffer, pk=pk)
    if request.method == "POST":
        form = JobOfferForm(request.POST, request.FILES, instance=offer)
        if form.is_valid():
            form.save()
            messages.success(request, "Offre mise à jour.")
            return redirect("services_app:admin_jobs_list")
    else:
        form = JobOfferForm(instance=offer)

    return render(request, "admin/jobs/form.html", {"form": form, "offer": offer})


@staff_member_required
def admin_jobs_applications_view(request, pk):
    offer = get_object_or_404(JobOffer, pk=pk)
    applications = offer.applications.all()
    return render(request, "admin/jobs/applications.html", {"offer": offer, "applications": applications})


@staff_member_required
def admin_job_application_update_view(request, pk):
    application = get_object_or_404(JobApplication, pk=pk)

    if request.method == "POST":
        form = JobApplicationStatusForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, "Statut mis à jour.")
            return redirect("services_app:admin_jobs_applications", pk=application.offer_id)
    else:
        form = JobApplicationStatusForm(instance=application)

    return render(request, "admin/jobs/application_update.html", {"application": application, "form": form})


@staff_member_required
def admin_jobs_detail_view(request, pk):
    offer = get_object_or_404(JobOffer, pk=pk)
    return render(request, "admin/jobs/detail.html", {"offer": offer})


@staff_member_required
def admin_jobs_delete_view(request, pk):
    offer = get_object_or_404(JobOffer, pk=pk)

    if request.method == "POST":
        offer.delete()
        messages.success(request, "Offre supprimée.")
        return redirect("services_app:admin_jobs_list")

    return render(request, "admin/jobs/confirm_delete.html", {"offer": offer})