from django.urls import path
from . import views

app_name = 'partners'

urlpatterns = [
    # Public
    path('programme/', views.partner_program_info, name='program_info'),
    path('postuler/', views.apply_as_partner, name='apply'),
    path('candidature/succes/', views.application_success, name='application_success'),
    
    # Espace partenaire
    path('dashboard/', views.partner_dashboard, name='dashboard'),
    path('contrats/', views.partner_contracts_list, name='contracts_list'),
    path('contrats/nouveau/', views.partner_submit_contract, name='submit_contract'),
    path('contrats/<int:pk>/', views.partner_contract_detail, name='contract_detail'),
    path('paiements/', views.partner_payments_history, name='payments_history'),
    
    # Admin
    path('admin/candidatures/', views.admin_applications_list, name='admin_applications'),
    path('admin/candidatures/<int:pk>/', views.admin_application_detail, name='admin_application_detail'),
    path('admin/partenaires/', views.admin_partners_list, name='admin_partners'),
    path('admin/partenaires/<int:pk>/', views.admin_partner_detail, name='admin_partner_detail'),
    path('admin/contrats/validation/', views.admin_contracts_validation, name='admin_contracts_validation'),
    path('admin/contrats/<int:pk>/valider/', views.admin_validate_contract, name='admin_validate_contract'),
    path('admin/partenaires/<int:partner_pk>/payer/', views.admin_pay_commission, name='admin_pay_commission'),
]