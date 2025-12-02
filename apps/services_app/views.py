from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Service, Offer, Training, TrainingEnrollment, OfferApplication
from .forms import OfferApplicationForm


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