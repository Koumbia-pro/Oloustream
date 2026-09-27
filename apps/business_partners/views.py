from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from apps.core.permissions import partner_required
from apps.core.utils import send_safely

from .forms import ContractSubmissionForm, PartnerApplicationForm
from .models import BusinessPartner, CommissionPayment, Contract, Region


# ==================== VUES PUBLIQUES ====================

def partner_program_info(request):
    """Page d'information sur le programme de partenariat"""
    stats = {
        'total_partners': BusinessPartner.objects.filter(is_active=True).count(),
        'total_contracts': Contract.objects.filter(status='completed').count(),
        'regions_covered': Region.objects.filter(partnerapplication__status='approved').distinct().count(),
    }
    return render(request, 'partners/program_info.html', {
        'priority_regions': Region.objects.filter(is_priority=True, active=True),
        'all_regions': Region.objects.filter(active=True),
        'stats': stats,
    })


def apply_as_partner(request):
    """Formulaire de candidature"""
    if request.method == 'POST':
        form = PartnerApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save()

            from apps.notifications.emailing import send_partner_application_notification
            send_safely(send_partner_application_notification, application)

            request.session['partner_application_name'] = application.full_name
            return redirect('partners:application_success')
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {
                'full_name': request.user.get_full_name(),
                'email': request.user.email,
                'phone': getattr(request.user, 'phone', ''),
            }
        form = PartnerApplicationForm(initial=initial)

    return render(request, 'partners/apply.html', {'form': form})


def application_success(request):
    """Page de confirmation après candidature"""
    return render(request, 'partners/application_success.html', {
        'applicant_name': request.session.pop('partner_application_name', ''),
    })


# ==================== ESPACE PARTENAIRE (connecté) ====================

@partner_required
def partner_dashboard(request):
    """Tableau de bord du partenaire"""
    partner = request.partner
    contracts = Contract.objects.filter(partner=partner)
    stats = contracts.aggregate(
        total_amount=Sum('contract_amount', filter=~Q(status__in=['cancelled', 'draft'])),
        total_commission=Sum('commission_amount', filter=~Q(status__in=['cancelled', 'draft'])),
        pending=Count('id', filter=Q(status='pending')),
        validated=Count('id', filter=Q(status__in=['validated', 'signed', 'in_progress', 'completed'])),
    )

    return render(request, 'partners/dashboard.html', {
        'partner': partner,
        'total_contracts': partner.total_contracts,
        'total_revenue': stats['total_amount'] or 0,
        'total_commission': stats['total_commission'] or 0,
        'pending_contracts': stats['pending'],
        'validated_contracts': stats['validated'],
        'pending_commission': partner.pending_commission,
        'recent_contracts': contracts.order_by('-created_at')[:5],
        'recent_payments': CommissionPayment.objects.filter(partner=partner).order_by('-paid_at')[:3],
    })


@partner_required
def partner_contracts_list(request):
    """Liste des contrats du partenaire"""
    partner = request.partner
    contracts = Contract.objects.filter(partner=partner).order_by('-created_at')

    status_filter = request.GET.get('status', '')
    if status_filter in dict(Contract.STATUS_CHOICES):
        contracts = contracts.filter(status=status_filter)

    return render(request, 'partners/contracts_list.html', {
        'partner': partner,
        'contracts': Paginator(contracts, 15).get_page(request.GET.get('page')),
        'status_choices': Contract.STATUS_CHOICES,
        'current_status': status_filter,
    })


@partner_required
def partner_submit_contract(request):
    """Soumettre un nouveau contrat"""
    partner = request.partner

    if request.method == 'POST':
        form = ContractSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            contract = form.save(commit=False)
            contract.partner = partner
            contract.commission_rate = partner.commission_rate
            contract.status = 'pending'
            contract.save()

            from apps.notifications.services import notify_new_contract_submission
            notify_new_contract_submission(contract)

            messages.success(
                request,
                f"Contrat soumis avec succès. Commission prévue : "
                f"{contract.commission_amount:,.0f} FCFA (après validation).".replace(",", " "),
            )
            return redirect('partners:contract_detail', pk=contract.pk)
    else:
        form = ContractSubmissionForm()

    return render(request, 'partners/submit_contract.html', {'partner': partner, 'form': form})


@partner_required
def partner_contract_detail(request, pk):
    """Détail d'un contrat"""
    contract = get_object_or_404(Contract, pk=pk, partner=request.partner)
    return render(request, 'partners/contract_detail.html', {
        'partner': request.partner,
        'contract': contract,
        'payments': contract.commission_payments.all(),
    })


@partner_required
def partner_payments_history(request):
    """Historique des paiements de commission"""
    partner = request.partner
    payments = CommissionPayment.objects.filter(partner=partner).order_by('-paid_at')
    return render(request, 'partners/payments_history.html', {
        'partner': partner,
        'payments': Paginator(payments, 20).get_page(request.GET.get('page')),
        'total_paid': partner.total_commission_paid,
        'pending_commission': partner.pending_commission,
    })
