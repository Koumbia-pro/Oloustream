from django.urls import path
from .views import (
    user_training_list_view,
    user_training_enroll_view,
    user_offer_list_view,
    user_offer_apply_view,
)

app_name = "services_app"

urlpatterns = [
    # Formations (utilisateur)
    path('trainings/', user_training_list_view, name='user_trainings_list'),
    path('trainings/<int:training_id>/enroll/', user_training_enroll_view, name='user_training_enroll'),

    # Offres (utilisateur)
    path('offers/', user_offer_list_view, name='user_offers_list'),
    path('offers/<int:offer_id>/apply/', user_offer_apply_view, name='user_offer_apply'),
]