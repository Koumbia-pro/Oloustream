# apps/studio/urls.py
from django.urls import path
from .views import (
    user_reservation_list_view,
    user_reservation_create_view,
    user_equipment_list_view,
    user_equipment_detail_view,
    user_equipment_reserve_view,
    user_studio_list_view,
    user_studio_detail_view,
    user_studio_reserve_view,
    user_project_reservation_create_view,
    admin_reservation_list_view,
    admin_reservation_detail_view,
)

app_name = "studio"

urlpatterns = [
    # Réservations utilisateur
    path("my/reservations/", user_reservation_list_view, name="user_reservations_list"),
    path("my/reservations/create/", user_reservation_create_view, name="user_reservations_create"),

    # Matériel
    path("equipments/", user_equipment_list_view, name="user_equipment_list"),
    path("equipments/<int:pk>/", user_equipment_detail_view, name="user_equipment_detail"),
    path("equipments/<int:pk>/reserve/", user_equipment_reserve_view, name="user_equipment_reserve"),

    # Studios
    path("studios/", user_studio_list_view, name="user_studio_list"),
    path("studios/<int:pk>/", user_studio_detail_view, name="user_studio_detail"),
    path("studios/<int:pk>/reserve/", user_studio_reserve_view, name="user_studio_reserve"),

    # Formulaire projet global (optionnel)
    path("reservations/projet/", user_project_reservation_create_view, name="user_project_reservation_create"),

    # Formulaire projet pour un studio précis (celui à utiliser partout)
    path("studios/<int:studio_pk>/projet/", user_project_reservation_create_view, name="user_studio_project_reservation"),

    # Admin
    path("admin/reservations/", admin_reservation_list_view, name="admin_reservations_list"),
    path("admin/reservations/<int:pk>/", admin_reservation_detail_view, name="admin_reservations_detail"),
]