from django.urls import path
from .views import (
    admin_job_application_update_view,
    admin_jobs_delete_view,
    admin_jobs_detail_view,
    user_training_list_view,
    user_training_enroll_view,
    user_offer_list_view,
    user_offer_apply_view,
)

from .views import (
    user_jobs_list_view, user_jobs_detail_view, user_jobs_apply_view,
    admin_jobs_list_view, admin_jobs_create_view, admin_jobs_edit_view,
    admin_jobs_applications_view,
    admin_jobs_detail_view,
    admin_jobs_delete_view,
)

app_name = "services_app"

urlpatterns = [
    # Formations (utilisateur)
    path('trainings/', user_training_list_view, name='user_trainings_list'),
    path('trainings/<int:training_id>/enroll/', user_training_enroll_view, name='user_training_enroll'),

    # Offres (utilisateur)
    path('offers/', user_offer_list_view, name='user_offers_list'),
    path('offers/<int:offer_id>/apply/', user_offer_apply_view, name='user_offer_apply'),

    # Jobs (user)
    path("jobs/", user_jobs_list_view, name="user_jobs_list"),
    path("jobs/<slug:slug>/", user_jobs_detail_view, name="user_jobs_detail"),
    path("jobs/<slug:slug>/apply/", user_jobs_apply_view, name="user_jobs_apply"),
    

    # Jobs (admin)
    path("admin/jobs/", admin_jobs_list_view, name="admin_jobs_list"),
    path("admin/jobs/create/", admin_jobs_create_view, name="admin_jobs_create"),
    path("admin/jobs/<int:pk>/edit/", admin_jobs_edit_view, name="admin_jobs_edit"),
    path("admin/jobs/<int:pk>/applications/", admin_jobs_applications_view, name="admin_jobs_applications"),
    path("admin/jobs/<int:pk>/", admin_jobs_detail_view, name="admin_jobs_detail"),
    path("admin/jobs/<int:pk>/delete/", admin_jobs_delete_view, name="admin_jobs_delete"),

    path("admin/job-applications/<int:pk>/update/", admin_job_application_update_view, name="admin_job_application_update"),
]