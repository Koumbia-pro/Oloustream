from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.utils import timezone
from .models import (
    PartnerApplication, BusinessPartner, Contract, 
    CommissionPayment, Region
)
from .forms import PartnerApplicationForm, ContractSubmissionForm
from apps.notifications.services import create_notification


# ==================== VUES PUBLIQUES ====================

def partner_program_info(request):
    """Page d'information sur le programme de partenariat"""
    priority_regions = Region.objects.filter(is_priority=True)
    all_regions = Region.objects.filter(active=True)
    
    # Statistiques globales (optionnel)
    stats = {
        'total_partners': BusinessPartner.objects.filter(is_active=True).count(),
        'total_contracts': Contract.objects.filter(status='completed').count(),
        'regions_covered': Region.objects.filter(
            partnerapplication__status='approved'
        ).distinct().count(),
    }
    
    context = {
        'priority_regions': priority_regions,
        'all_regions': all_regions,
        'stats': stats,
    }
    return render(request, 'partners/program_info.html', context)


def apply_as_partner(request):
    """Formulaire de candidature"""
    if request.method == 'POST':
        form = PartnerApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save()
            
            # Notification email à l'équipe
            from apps.notifications.emailing import send_partner_application_notification
            send_partner_application_notification(application)
            
            # Message de succès
            messages.success(
                request,
                "✅ Votre candidature a été soumise avec succès ! "
                "Notre équipe vous contactera dans les 48-72h."
            )
            return redirect('partners:application_success')
    else:
        form = PartnerApplicationForm()
    
    return render(request, 'partners/apply.html', {'form': form})


def application_success(request):
    """Page de confirmation après candidature"""
    return render(request, 'partners/application_success.html')


# ==================== ESPACE PARTENAIRE (connecté) ====================

@login_required
def partner_dashboard(request):
    """Tableau de bord du partenaire"""
    try:
        partner = request.user.business_partner
    except BusinessPartner.DoesNotExist:
        messages.error(request, "Vous n'êtes pas enregistré comme partenaire d'affaires.")
        return redirect('core:home')
    
    # Statistiques
    contracts_stats = Contract.objects.filter(partner=partner).aggregate(
        total_amount=Sum('contract_amount'),
        total_commission=Sum('commission_amount'),
    )
    
    # Derniers contrats
    recent_contracts = Contract.objects.filter(partner=partner).order_by('-created_at')[:5]
    
    # Commission en attente
    pending_commission = partner.pending_commission
    
    context = {
        'partner': partner,
        'total_contracts': partner.total_contracts,
        'total_revenue': contracts_stats['total_amount'] or 0,
        'total_commission': contracts_stats['total_commission'] or 0,
        'pending_commission': pending_commission,
        'recent_contracts': recent_contracts,
    }
    return render(request, 'partners/dashboard.html', context)


@login_required
def partner_contracts_list(request):
    """Liste des contrats du partenaire"""
    try:
        partner = request.user.business_partner
    except BusinessPartner.DoesNotExist:
        messages.error(request, "Accès non autorisé.")
        return redirect('core:home')
    
    contracts = Contract.objects.filter(partner=partner).order_by('-created_at')
    
    # Filtres
    status_filter = request.GET.get('status')
    if status_filter:
        contracts = contracts.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(contracts, 15)
    page = request.GET.get('page')
    contracts = paginator.get_page(page)
    
    context = {
        'partner': partner,
        'contracts': contracts,
        'status_choices': Contract.STATUS_CHOICES,
    }
    return render(request, 'partners/contracts_list.html', context)


@login_required
def partner_submit_contract(request):
    """Soumettre un nouveau contrat"""
    try:
        partner = request.user.business_partner
    except BusinessPartner.DoesNotExist:
        messages.error(request, "Accès non autorisé.")
        return redirect('core:home')
    
    if request.method == 'POST':
        form = ContractSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            contract = form.save(commit=False)
            contract.partner = partner
            contract.commission_rate = partner.commission_rate
            contract.status = 'pending'
            contract.save()
            
            # Notification à l'admin
            from apps.notifications.services import notify_new_contract_submission
            notify_new_contract_submission(contract)
            
            messages.success(
                request,
                f"✅ Contrat soumis avec succès ! "
                f"Commission prévue : {contract.commission_amount:,.0f} FCFA"
            )
            return redirect('partners:contracts_list')
    else:
        form = ContractSubmissionForm()
    
    context = {
        'partner': partner,
        'form': form,
    }
    return render(request, 'partners/submit_contract.html', context)


@login_required
def partner_contract_detail(request, pk):
    """Détail d'un contrat"""
    try:
        partner = request.user.business_partner
    except BusinessPartner.DoesNotExist:
        messages.error(request, "Accès non autorisé.")
        return redirect('core:home')
    
    contract = get_object_or_404(Contract, pk=pk, partner=partner)
    
    context = {
        'partner': partner,
        'contract': contract,
    }
    return render(request, 'partners/contract_detail.html', context)


@login_required
def partner_payments_history(request):
    """Historique des paiements de commission"""
    try:
        partner = request.user.business_partner
    except BusinessPartner.DoesNotExist:
        messages.error(request, "Accès non autorisé.")
        return redirect('core:home')
    
    payments = CommissionPayment.objects.filter(partner=partner).order_by('-paid_at')
    
    # Pagination
    paginator = Paginator(payments, 20)
    page = request.GET.get('page')
    payments = paginator.get_page(page)
    
    context = {
        'partner': partner,
        'payments': payments,
    }
    return render(request, 'partners/payments_history.html', context)


# ==================== VUES ADMIN ====================

@login_required
def admin_applications_list(request):
    """Liste des candidatures (admin)"""
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('core:home')
    
    applications = PartnerApplication.objects.all().order_by('-created_at')
    
    # Filtres
    status_filter = request.GET.get('status')
    city_filter = request.GET.get('city')
    
    if status_filter:
        applications = applications.filter(status=status_filter)
    if city_filter:
        applications = applications.filter(city_id=city_filter)
    
    # Pagination
    paginator = Paginator(applications, 20)
    page = request.GET.get('page')
    applications = paginator.get_page(page)
    
    context = {
        'applications': applications,
        'regions': Region.objects.all(),
        'status_choices': PartnerApplication.STATUS_CHOICES,
    }
    return render(request, 'admin/partners/applications_list.html', context)


@login_required
def admin_application_detail(request, pk):
    """Détail d'une candidature (admin)"""
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('core:home')
    
    application = get_object_or_404(PartnerApplication, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            # Créer le compte partenaire
            from .services import activate_partner
            partner = activate_partner(application, request.user)
            
            messages.success(
                request,
                f"✅ Partenaire activé ! Code : {partner.partner_code}"
            )
            return redirect('admin:partners:detail', pk=partner.pk)
        
        elif action == 'reject':
            application.status = 'rejected'
            application.reviewed_by = request.user
            application.reviewed_at = timezone.now()
            application.save()
            
            messages.warning(request, "❌ Candidature rejetée.")
            return redirect('admin:partners:applications')
        
        elif action == 'update_status':
            new_status = request.POST.get('status')
            application.status = new_status
            application.save()
            messages.success(request, "Statut mis à jour.")
    
    context = {
        'application': application,
    }
    return render(request, 'admin/partners/application_detail.html', context)


@login_required
def admin_partners_list(request):
    """Liste des partenaires actifs (admin)"""
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('core:home')
    
    partners = BusinessPartner.objects.all().order_by('-total_revenue')
    
    # Filtres
    active_filter = request.GET.get('active')
    if active_filter == 'true':
        partners = partners.filter(is_active=True)
    elif active_filter == 'false':
        partners = partners.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(partners, 20)
    page = request.GET.get('page')
    partners = paginator.get_page(page)
    
    context = {
        'partners': partners,
    }
    return render(request, 'admin/partners/partners_list.html', context)


@login_required
def admin_partner_detail(request, pk):
    """Détail d'un partenaire (admin)"""
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('core:home')
    
    partner = get_object_or_404(BusinessPartner, pk=pk)
    contracts = Contract.objects.filter(partner=partner).order_by('-created_at')[:10]
    
    context = {
        'partner': partner,
        'contracts': contracts,
    }
    return render(request, 'admin/partners/partner_detail.html', context)


@login_required
def admin_contracts_validation(request):
    """Liste des contrats à valider (admin)"""
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('core:home')
    
    contracts = Contract.objects.filter(
        status='pending'
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(contracts, 20)
    page = request.GET.get('page')
    contracts = paginator.get_page(page)
    
    context = {
        'contracts': contracts,
    }
    return render(request, 'admin/partners/contracts_validation.html', context)


@login_required
def admin_validate_contract(request, pk):
    """Valider ou rejeter un contrat (admin)"""
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('core:home')
    
    contract = get_object_or_404(Contract, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'validate':
            contract.status = 'validated'
            contract.validated_by = request.user
            contract.validated_at = timezone.now()
            contract.save()
            
            # Mettre à jour les stats du partenaire
            partner = contract.partner
            partner.total_contracts += 1
            partner.total_revenue += contract.contract_amount
            partner.total_commission_earned += contract.commission_amount
            partner.last_contract_at = timezone.now()
            partner.save()
            
            # Notification au partenaire
            from apps.notifications.services import notify_contract_validated
            notify_contract_validated(contract)
            
            messages.success(request, f"✅ Contrat validé ! Commission : {contract.commission_amount:,.0f} FCFA")
        
        elif action == 'reject':
            contract.status = 'cancelled'
            contract.save()
            messages.warning(request, "❌ Contrat rejeté.")
        
        return redirect('admin:partners:contracts_validation')
    
    context = {
        'contract': contract,
    }
    return render(request, 'admin/partners/contract_validation_detail.html', context)


@login_required
def admin_pay_commission(request, partner_pk):
    """Enregistrer un paiement de commission (admin)"""
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('core:home')
    
    partner = get_object_or_404(BusinessPartner, pk=partner_pk)
    
    # Contrats non payés
    unpaid_contracts = Contract.objects.filter(
        partner=partner,
        status__in=['validated', 'completed'],
        commission_payments__isnull=True
    )
    
    if request.method == 'POST':
        amount = float(request.POST.get('amount', 0))
        method = request.POST.get('payment_method')
        reference = request.POST.get('reference', '')
        contract_ids = request.POST.getlist('contracts')
        
        if amount > 0:
            payment = CommissionPayment.objects.create(
                partner=partner,
                amount=amount,
                payment_method=method,
                reference=reference,
                created_by=request.user
            )
            
            # Associer les contrats
            if contract_ids:
                payment.contracts.set(contract_ids)
            
            # Mettre à jour le partenaire
            partner.total_commission_paid += amount
            partner.save()
            
            messages.success(request, f"✅ Paiement de {amount:,.0f} FCFA enregistré.")
            return redirect('admin:partners:detail', pk=partner.pk)
    
    context = {
        'partner': partner,
        'unpaid_contracts': unpaid_contracts,
        'pending_amount': partner.pending_commission,
    }
    return render(request, 'admin/partners/pay_commission.html', context)