from django.urls import path

from . import views

app_name = 'partners'

# L'administration des partenaires se fait dans le dashboard (apps/dashboard).
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
]
