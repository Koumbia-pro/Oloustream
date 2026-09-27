from django.urls import path

from . import views

app_name = "services_app"

urlpatterns = [
    # Formations (utilisateur)
    path('trainings/', views.user_training_list_view, name='user_trainings_list'),
    path('trainings/<int:training_id>/enroll/', views.user_training_enroll_view, name='user_training_enroll'),

    # Offres (utilisateur)
    path('offers/', views.user_offer_list_view, name='user_offers_list'),
    path('offers/<int:offer_id>/apply/', views.user_offer_apply_view, name='user_offer_apply'),

    # Emplois & stages (utilisateur)
    path("jobs/", views.user_jobs_list_view, name="user_jobs_list"),
    path("jobs/<slug:slug>/", views.user_jobs_detail_view, name="user_jobs_detail"),
    path("jobs/<slug:slug>/apply/", views.user_jobs_apply_view, name="user_jobs_apply"),

    # Emplois & stages (admin)
    path("admin/jobs/", views.admin_jobs_list_view, name="admin_jobs_list"),
    path("admin/jobs/create/", views.admin_jobs_create_view, name="admin_jobs_create"),
    path("admin/jobs/<int:pk>/", views.admin_jobs_detail_view, name="admin_jobs_detail"),
    path("admin/jobs/<int:pk>/edit/", views.admin_jobs_edit_view, name="admin_jobs_edit"),
    path("admin/jobs/<int:pk>/applications/", views.admin_jobs_applications_view, name="admin_jobs_applications"),
    path("admin/jobs/<int:pk>/delete/", views.admin_jobs_delete_view, name="admin_jobs_delete"),
    path("admin/job-applications/<int:pk>/update/", views.admin_job_application_update_view,
         name="admin_job_application_update"),
]
