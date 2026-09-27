"""Administration du programme de partenaires d'affaires."""
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.business_partners.models import (
    BusinessPartner, CommissionPayment, Contract, PartnerApplication, Region,
)
from apps.business_partners.services import (
    PartnerActionError, activate_partner, cancel_contract, record_commission_payment, validate_contract,
)
from apps.core.utils import parse_int, querystring_without_page
from apps.core.validators import validate_document

__all__ = [
    "partner_applications_list", "partner_application_detail", "partner_application_approve",
    "partner_application_reject", "partner_application_update_status",
    "business_partners_list", "business_partner_detail", "business_partner_toggle_active",
    "partner_contracts_list", "partner_contract_detail", "partner_contract_validate", "partner_contract_reject",
    "partner_payments_list", "partner_payment_create",
]


# ==================== CANDIDATURES ====================

@staff_member_required
def partner_applications_list(request):
    applications = PartnerApplication.objects.select_related("city").order_by("-created_at")
    status = request.GET.get("status", "")
    city = request.GET.get("city", "")
    network = request.GET.get("network", "")
    search = request.GET.get("search", "").strip()

    if status in dict(PartnerApplication.STATUS_CHOICES):
        applications = applications.filter(status=status)
    if parse_int(city):
        applications = applications.filter(city_id=parse_int(city))
    if network in dict(PartnerApplication.NETWORK_STRENGTH):
        applications = applications.filter(network_strength=network)
    if search:
        applications = applications.filter(
            Q(full_name__icontains=search) | Q(phone__icontains=search) | Q(email__icontains=search)
        )

    stats = PartnerApplication.objects.aggregate(
        total=Count("id"),
        pending=Count("id", filter=Q(status="pending")),
        reviewing=Count("id", filter=Q(status__in=["reviewing", "interview"])),
        approved=Count("id", filter=Q(status="approved")),
        rejected=Count("id", filter=Q(status="rejected")),
    )
    return render(request, "admin/business_partners/applications_list.html", {
        "applications": Paginator(applications, 15).get_page(request.GET.get("page")),
        "stats": stats,
        "regions": Region.objects.all(),
        "status_choices": PartnerApplication.STATUS_CHOICES,
        "network_choices": PartnerApplication.NETWORK_STRENGTH,
        "current_status": status,
        "current_city": city,
        "current_network": network,
        "search_query": search,
        "base_querystring": querystring_without_page(request),
    })


@staff_member_required
def partner_application_detail(request, pk):
    application = get_object_or_404(PartnerApplication.objects.select_related("city", "reviewed_by"), pk=pk)
    return render(request, "admin/business_partners/application_detail.html", {
        "application": application,
        "status_choices": [c for c in PartnerApplication.STATUS_CHOICES if c[0] != "approved"],
        "partner": BusinessPartner.objects.filter(application=application).first(),
    })


@staff_member_required
@require_POST
def partner_application_approve(request, pk):
    application = get_object_or_404(PartnerApplication, pk=pk)
    if application.status == "approved":
        messages.warning(request, "Cette candidature est déjà approuvée.")
        return redirect("dashboard:partner_application_detail", pk=pk)
    try:
        partner = activate_partner(application, request.user)
    except PartnerActionError as exc:
        messages.error(request, str(exc))
        return redirect("dashboard:partner_application_detail", pk=pk)
    messages.success(
        request,
        f"Partenaire activé (code {partner.partner_code}). Un email lui permettant de créer "
        f"son mot de passe a été envoyé à {partner.user.email}.",
    )
    return redirect("dashboard:business_partner_detail", pk=partner.pk)


@staff_member_required
@require_POST
def partner_application_reject(request, pk):
    application = get_object_or_404(PartnerApplication, pk=pk)
    if application.status == "approved":
        messages.error(request, "Une candidature approuvée ne peut pas être rejetée. Suspendez plutôt le partenaire.")
        return redirect("dashboard:partner_application_detail", pk=pk)

    reason = request.POST.get("reason", "").strip()
    now = timezone.now()
    application.status = "rejected"
    application.reviewed_by = request.user
    application.reviewed_at = now
    note = f"[{timezone.localtime(now):%d/%m/%Y %H:%M}] Rejetée par {request.user.get_full_name() or request.user.username}"
    if reason:
        note += f" — Raison : {reason}"
    application.internal_notes = f"{application.internal_notes}\n{note}".strip()
    application.save()
    messages.warning(request, f"Candidature de {application.full_name} rejetée.")
    return redirect("dashboard:partner_applications_list")


@staff_member_required
@require_POST
def partner_application_update_status(request, pk):
    application = get_object_or_404(PartnerApplication, pk=pk)
    new_status = request.POST.get("status")
    allowed = {"pending", "reviewing", "interview"}
    notes = request.POST.get("internal_notes")
    if notes is not None:
        application.internal_notes = notes
    if new_status in allowed and application.status != "approved":
        application.status = new_status
        messages.success(request, f"Statut mis à jour : {application.get_status_display()}")
    elif new_status:
        messages.error(request, "Statut invalide. Utilisez les boutons Approuver / Rejeter.")
    application.save()
    return redirect("dashboard:partner_application_detail", pk=pk)


# ==================== PARTENAIRES ACTIFS ====================

@staff_member_required
def business_partners_list(request):
    partners = BusinessPartner.objects.select_related("user", "application", "application__city").order_by("-total_revenue")
    active_filter = request.GET.get("active", "")
    city_filter = request.GET.get("city", "")
    search = request.GET.get("search", "").strip()

    if active_filter == "true":
        partners = partners.filter(is_active=True)
    elif active_filter == "false":
        partners = partners.filter(is_active=False)
    if parse_int(city_filter):
        partners = partners.filter(application__city_id=parse_int(city_filter))
    if search:
        partners = partners.filter(
            Q(partner_code__icontains=search) | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search) | Q(user__email__icontains=search)
        )

    stats = BusinessPartner.objects.aggregate(
        total_partners=Count("id"),
        active_partners=Count("id", filter=Q(is_active=True)),
        total_revenue=Sum("total_revenue"),
        total_commission=Sum("total_commission_earned"),
        total_paid=Sum("total_commission_paid"),
    )
    stats["pending_commission"] = (stats["total_commission"] or 0) - (stats["total_paid"] or 0)

    return render(request, "admin/business_partners/partners_list.html", {
        "partners": Paginator(partners, 15).get_page(request.GET.get("page")),
        "stats": stats,
        "regions": Region.objects.all(),
        "current_active": active_filter,
        "current_city": city_filter,
        "search_query": search,
        "base_querystring": querystring_without_page(request),
    })


@staff_member_required
def business_partner_detail(request, pk):
    partner = get_object_or_404(BusinessPartner.objects.select_related("user", "application", "application__city"), pk=pk)
    contracts = Contract.objects.filter(partner=partner)
    return render(request, "admin/business_partners/partner_detail.html", {
        "partner": partner,
        "contracts": contracts.order_by("-created_at")[:10],
        "payments": CommissionPayment.objects.filter(partner=partner).order_by("-paid_at")[:5],
        "contracts_stats": contracts.aggregate(
            total=Count("id"),
            validated=Count("id", filter=Q(status="validated")),
            completed=Count("id", filter=Q(status="completed")),
            pending=Count("id", filter=Q(status="pending")),
        ),
    })


@staff_member_required
@require_POST
def business_partner_toggle_active(request, pk):
    partner = get_object_or_404(BusinessPartner, pk=pk)
    if partner.is_active:
        partner.is_active = False
        partner.suspension_reason = request.POST.get("reason", "").strip() or "Suspendu par l'administration"
        messages.warning(request, f"Partenaire {partner.partner_code} suspendu.")
    else:
        partner.is_active = True
        partner.suspension_reason = ""
        messages.success(request, f"Partenaire {partner.partner_code} réactivé.")
    partner.save(update_fields=["is_active", "suspension_reason"])
    return redirect("dashboard:business_partner_detail", pk=pk)


# ==================== CONTRATS ====================

@staff_member_required
def partner_contracts_list(request):
    contracts = Contract.objects.select_related("partner", "partner__user").order_by("-created_at")
    status = request.GET.get("status", "")
    partner = request.GET.get("partner", "")
    search = request.GET.get("search", "").strip()

    if status in dict(Contract.STATUS_CHOICES):
        contracts = contracts.filter(status=status)
    if parse_int(partner):
        contracts = contracts.filter(partner_id=parse_int(partner))
    if search:
        contracts = contracts.filter(
            Q(client_name__icontains=search) | Q(partner__partner_code__icontains=search)
            | Q(service_type__icontains=search)
        )

    stats = Contract.objects.aggregate(
        total=Count("id"),
        pending=Count("id", filter=Q(status="pending")),
        validated=Count("id", filter=Q(status="validated")),
        completed=Count("id", filter=Q(status="completed")),
        total_amount=Sum("contract_amount", filter=~Q(status="cancelled")),
        total_commission=Sum("commission_amount", filter=~Q(status="cancelled")),
    )
    return render(request, "admin/business_partners/contracts_list.html", {
        "contracts": Paginator(contracts, 20).get_page(request.GET.get("page")),
        "stats": stats,
        "partners": BusinessPartner.objects.filter(is_active=True).select_related("user"),
        "status_choices": Contract.STATUS_CHOICES,
        "current_status": status,
        "current_partner": partner,
        "search_query": search,
        "base_querystring": querystring_without_page(request),
    })


@staff_member_required
def partner_contract_detail(request, pk):
    contract = get_object_or_404(
        Contract.objects.select_related("partner", "partner__user", "validated_by"), pk=pk
    )
    return render(request, "admin/business_partners/contract_detail.html", {
        "contract": contract,
        "payments": contract.commission_payments.all(),
    })


@staff_member_required
@require_POST
def partner_contract_validate(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    try:
        contract = validate_contract(contract, request.user)
    except PartnerActionError as exc:
        messages.warning(request, str(exc))
        return redirect("dashboard:partner_contract_detail", pk=pk)
    messages.success(
        request,
        f"Contrat validé. Commission de {contract.commission_amount:,.0f} FCFA attribuée "
        f"à {contract.partner.partner_code}.".replace(",", " "),
    )
    return redirect("dashboard:partner_contract_detail", pk=pk)


@staff_member_required
@require_POST
def partner_contract_reject(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    try:
        cancel_contract(contract, request.user)
    except PartnerActionError as exc:
        messages.warning(request, str(exc))
        return redirect("dashboard:partner_contract_detail", pk=pk)
    messages.warning(request, f"Contrat de {contract.client_name} annulé.")
    return redirect("dashboard:partner_contracts_list")


# ==================== PAIEMENTS ====================

@staff_member_required
def partner_payments_list(request):
    payments = CommissionPayment.objects.select_related("partner", "partner__user", "created_by").order_by("-paid_at")
    partner_filter = request.GET.get("partner", "")
    method = request.GET.get("method", "")
    if parse_int(partner_filter):
        payments = payments.filter(partner_id=parse_int(partner_filter))
    if method in dict(CommissionPayment.PAYMENT_METHODS):
        payments = payments.filter(payment_method=method)

    stats = CommissionPayment.objects.aggregate(total_payments=Count("id"), total_amount=Sum("amount"))
    totals = BusinessPartner.objects.aggregate(earned=Sum("total_commission_earned"), paid=Sum("total_commission_paid"))
    return render(request, "admin/business_partners/payments_list.html", {
        "payments": Paginator(payments, 20).get_page(request.GET.get("page")),
        "stats": stats,
        "pending_amount": (totals["earned"] or 0) - (totals["paid"] or 0),
        "partners": BusinessPartner.objects.select_related("user"),
        "method_choices": CommissionPayment.PAYMENT_METHODS,
        "current_partner": partner_filter,
        "current_method": method,
        "base_querystring": querystring_without_page(request),
    })


@staff_member_required
def partner_payment_create(request, partner_pk):
    partner = get_object_or_404(BusinessPartner.objects.select_related("user"), pk=partner_pk)
    unpaid_contracts = Contract.objects.filter(
        partner=partner, status__in=["validated", "signed", "in_progress", "completed"],
    ).exclude(commission_payments__isnull=False).order_by("-created_at")

    form_data = {}
    if request.method == "POST":
        form_data = request.POST
        receipt = request.FILES.get("receipt")
        try:
            if receipt:
                validate_document(receipt)
            payment = record_commission_payment(
                partner,
                amount=request.POST.get("amount"),
                method=request.POST.get("payment_method", ""),
                reference=request.POST.get("reference", "").strip(),
                notes=request.POST.get("notes", "").strip(),
                contract_ids=[i for i in request.POST.getlist("contracts") if i.isdigit()],
                receipt=receipt,
                admin_user=request.user,
            )
        except PartnerActionError as exc:
            messages.error(request, str(exc))
        except ValidationError as exc:  # reçu invalide
            messages.error(request, " ".join(exc.messages))
        else:
            messages.success(
                request,
                f"Paiement de {payment.amount:,.0f} FCFA enregistré pour {partner.partner_code}.".replace(",", " "),
            )
            return redirect("dashboard:business_partner_detail", pk=partner_pk)

    return render(request, "admin/business_partners/payment_create.html", {
        "partner": partner,
        "unpaid_contracts": unpaid_contracts,
        "pending_amount": partner.pending_commission,
        "method_choices": CommissionPayment.PAYMENT_METHODS,
        "form_data": form_data,
    })
