from django.urls import path
from . import views
from .views import (
    dashboard_view,
    # Employés
    employee_list_view,
    employee_create_view,
    employee_update_view,
    employee_detail_view,
    employee_delete_view,
    employee_change_password_view,
    employee_export_excel_view, 
    # Équipements
    equipment_list_view,
    equipment_create_view,
    equipment_update_view,
    equipment_delete_view,
    equipment_detail_view, 
    equipment_export_excel_view,
    # Réservations
    reservation_list_view,
    reservation_detail_view,
    reservation_export_excel_view,
    reservation_quick_cancel_view,
    reservation_set_status_view, 
    # Services
    service_list_view,
    service_create_view,
    service_update_view,
    service_delete_view,
    service_export_excel_view,
    service_detail_view,
    # Offres
    offer_list_view,
    offer_create_view,
    offer_update_view,
    offer_delete_view,
    offer_export_excel_view,
    offer_detail_view,
    # Formations
    training_list_view,
    training_create_view,
    training_update_view,
    training_delete_view,
    training_detail_view,
    training_export_excel_view,
    # Partenaires
    partner_list_view,
    partner_create_view,
    partner_update_view,
    partner_delete_view,
    partner_detail_view,
    partner_export_excel_view,
    # Studios
    studio_list_view,
    studio_create_view,
    studio_detail_view,
    studio_update_view,
    studio_delete_view,

)

app_name = "dashboard"

urlpatterns = [
    path('', dashboard_view, name='index'),

    # Employés
    path('employees/', employee_list_view, name='employees_list'),
    path('employees/create/', employee_create_view, name='employees_create'),
    path('employees/<int:user_id>/edit/', employee_update_view, name='employees_edit'),
    path('employees/<int:user_id>/delete/', employee_delete_view, name='employees_delete'),
    path('employees/<int:user_id>/', employee_detail_view, name='employees_detail'),
    path('employees/<int:user_id>/password/', employee_change_password_view, name='employees_change_password'),
    path('employees/export/excel/', employee_export_excel_view, name='employees_export_excel'),

    # Équipements
    path('equipments/', equipment_list_view, name='equipments_list'),
    path('equipments/create/', equipment_create_view, name='equipments_create'),
    path('equipments/<int:equipment_id>/', equipment_detail_view, name='equipments_detail'),
    path('equipments/<int:equipment_id>/edit/', equipment_update_view, name='equipments_edit'),
    path('equipments/<int:equipment_id>/delete/', equipment_delete_view, name='equipments_delete'),
    path('equipments/export/excel/', equipment_export_excel_view, name='equipments_export_excel'),

    # Réservations
    path('reservations/', reservation_list_view, name='reservations_list'),
    path('reservations/<int:reservation_id>/', reservation_detail_view, name='reservations_detail'),
    path('reservations/export/excel/', reservation_export_excel_view, name='reservations_export_excel'),
    path('reservations/<int:reservation_id>/cancel/', reservation_quick_cancel_view, name='reservations_quick_cancel'),
     # ✅ Action POST unique : confirmer / refuser / terminer / annuler
    path(
        'reservations/<int:reservation_id>/set-status/',
        reservation_set_status_view,
        name='reservations_set_status',
    ),


    # Services
    path('services/', service_list_view, name='services_list'),
    path('services/create/', service_create_view, name='services_create'),
    path('services/<int:service_id>/', service_detail_view, name='services_detail'),
    path('services/<int:service_id>/edit/', service_update_view, name='services_edit'),
    path('services/<int:service_id>/delete/', service_delete_view, name='services_delete'),
    path('services/export/excel/', service_export_excel_view, name='services_export_excel'),

    # Offres
    path('offers/', offer_list_view, name='offers_list'),
    path('offers/create/', offer_create_view, name='offers_create'),
    path('offers/<int:offer_id>/', offer_detail_view, name='offers_detail'),
    path('offers/<int:offer_id>/edit/', offer_update_view, name='offers_edit'),
    path('offers/<int:offer_id>/delete/', offer_delete_view, name='offers_delete'),
    path('offers/export/excel/', offer_export_excel_view, name='offers_export_excel'),

    # Formations
    path('trainings/', training_list_view, name='trainings_list'),
    path('trainings/create/', training_create_view, name='trainings_create'),
    path('trainings/<int:training_id>/', training_detail_view, name='trainings_detail'),
    path('trainings/<int:training_id>/edit/', training_update_view, name='trainings_edit'),
    path('trainings/<int:training_id>/delete/', training_delete_view, name='trainings_delete'),
    path('trainings/export/excel/', training_export_excel_view, name='trainings_export_excel'),

    # Partenaires
    path('partners/', partner_list_view, name='partners_list'),
    path('partners/create/', partner_create_view, name='partners_create'),
    path('partners/<int:partner_id>/', partner_detail_view, name='partners_detail'),
    path('partners/<int:partner_id>/edit/', partner_update_view, name='partners_edit'),
    path('partners/<int:partner_id>/delete/', partner_delete_view, name='partners_delete'),
    path('partners/export/excel/', partner_export_excel_view, name='partners_export_excel'),

    # Studios
    path('studios/', studio_list_view, name='studios_list'),
    path('studios/create/', studio_create_view, name='studios_create'),
    path('studios/<int:studio_id>/', studio_detail_view, name='studios_detail'),
    path('studios/<int:studio_id>/edit/', studio_update_view, name='studios_edit'),
    path('studios/<int:studio_id>/delete/', studio_delete_view, name='studios_delete'),


    # Candidatures
    path('partenaires/candidatures/', 
         views.partner_applications_list, 
         name='partner_applications_list'),
    path('partenaires/candidatures/<int:pk>/', 
         views.partner_application_detail, 
         name='partner_application_detail'),
    path('partenaires/candidatures/<int:pk>/approuver/', 
         views.partner_application_approve, 
         name='partner_application_approve'),
    path('partenaires/candidatures/<int:pk>/rejeter/', 
         views.partner_application_reject, 
         name='partner_application_reject'),
    path('partenaires/candidatures/<int:pk>/statut/', 
         views.partner_application_update_status, 
         name='partner_application_update_status'),
    
    # Partenaires actifs
    path('partenaires/liste/', 
         views.business_partners_list, 
         name='business_partners_list'),
    path('partenaires/<int:pk>/', 
         views.business_partner_detail, 
         name='business_partner_detail'),
    path('partenaires/<int:pk>/toggle/', 
         views.business_partner_toggle_active, 
         name='business_partner_toggle_active'),
    
    # Contrats
    path('partenaires/contrats/', 
         views.partner_contracts_list, 
         name='partner_contracts_list'),
    path('partenaires/contrats/<int:pk>/', 
         views.partner_contract_detail, 
         name='partner_contract_detail'),
    path('partenaires/contrats/<int:pk>/valider/', 
         views.partner_contract_validate, 
         name='partner_contract_validate'),
    path('partenaires/contrats/<int:pk>/rejeter/', 
         views.partner_contract_reject, 
         name='partner_contract_reject'),
    
    # Paiements
    path('partenaires/paiements/', 
         views.partner_payments_list, 
         name='partner_payments_list'),
    path('partenaires/<int:partner_pk>/payer/', 
         views.partner_payment_create, 
         name='partner_payment_create'),
]