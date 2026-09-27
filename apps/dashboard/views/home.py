from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q, Sum
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.business_partners.models import BusinessPartner, Contract, PartnerApplication
from apps.core.models import ContactRequest
from apps.notifications.models import Notification, NotificationTypeChoices
from apps.payments.models import Payment, PaymentStatus
from apps.services_app.models import JobApplication, JobOffer, Partner, Service, Training
from apps.studio.choices import EquipmentStatus, ReservationStatus
from apps.studio.models import Equipment, Reservation, Studio

__all__ = ["dashboard_view"]

MONTHS_FR = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def _period_bounds(period, now):
    today_start = timezone.localtime(now).replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "today":
        return today_start, now
    if period == "week":
        return today_start - timedelta(days=today_start.weekday()), now
    if period == "month":
        return today_start.replace(day=1), now
    if period == "year":
        return today_start.replace(month=1, day=1), now
    return None, None


def _last_months(now, count=6):
    """Premiers jours des `count` derniers mois (du plus ancien au plus récent)."""
    local = timezone.localtime(now)
    year, month = local.year, local.month
    months = []
    for _ in range(count):
        months.append((year, month))
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    return list(reversed(months))


def _plural(count, word, plural=None):
    return f"{count} {word if count == 1 else (plural or word + 's')}"


@staff_member_required
def dashboard_view(request):
    """Tableau de bord principal : indicateurs, alertes et activité récente."""
    period = request.GET.get("period", "all")
    now = timezone.now()
    start_date, end_date = _period_bounds(period, now)

    paid = Payment.objects.filter(status=PaymentStatus.PAID)
    reservations_qs = Reservation.objects.all()
    if start_date:
        paid_period = paid.filter(created_at__range=(start_date, end_date))
        reservations_qs = reservations_qs.filter(created_at__range=(start_date, end_date))
    else:
        paid_period = paid

    total_revenue = paid_period.aggregate(total=Sum("amount"))["total"] or 0
    recent_revenue = paid.filter(created_at__gte=now - timedelta(days=30)).aggregate(total=Sum("amount"))["total"] or 0

    equipment_stats = Equipment.objects.aggregate(
        total=Count("id"),
        available=Count("id", filter=Q(status=EquipmentStatus.AVAILABLE)),
        maintenance=Count("id", filter=Q(status=EquipmentStatus.MAINTENANCE)),
    )

    status_counts = dict(
        Reservation.objects.values_list("status").annotate(c=Count("id")).values_list("status", "c")
    )
    reservations_by_status = {
        "pending": status_counts.get(ReservationStatus.PENDING, 0),
        "confirmed": status_counts.get(ReservationStatus.CONFIRMED, 0),
        "completed": status_counts.get(ReservationStatus.COMPLETED, 0),
        "cancelled": status_counts.get(ReservationStatus.CANCELLED, 0),
        "rejected": status_counts.get(ReservationStatus.REJECTED, 0),
    }

    # Partenaires d'affaires
    pending_applications = PartnerApplication.objects.filter(status="pending").count()
    pending_contracts = Contract.objects.filter(status="pending").count()
    bp_stats = BusinessPartner.objects.aggregate(
        earned=Sum("total_commission_earned"), paid=Sum("total_commission_paid"),
        active=Count("id", filter=Q(is_active=True)),
    )
    total_commission_earned = bp_stats["earned"] or 0
    total_commission_paid = bp_stats["paid"] or 0

    # Évolution du chiffre d'affaires sur 6 mois (mois calendaires)
    months = _last_months(now)
    first_year, first_month = months[0]
    first_day = timezone.localtime(now).replace(year=first_year, month=first_month, day=1,
                                                hour=0, minute=0, second=0, microsecond=0)
    # Agrégation en Python : TruncMonth est peu fiable sur MySQL sans tables de fuseaux horaires
    monthly = {}
    for created_at, amount in paid.filter(created_at__gte=first_day).values_list("created_at", "amount"):
        local = timezone.localtime(created_at)
        key = (local.year, local.month)
        monthly[key] = monthly.get(key, 0) + (amount or 0)
    revenue_chart_data = [
        {"month": f"{MONTHS_FR[m - 1]} {y}", "revenue": float(monthly.get((y, m), 0) or 0)}
        for y, m in months
    ]

    # Alertes
    unread_messages = Notification.objects.filter(
        user=request.user, notification_type=NotificationTypeChoices.MESSAGE_RECEIVED, is_read=False
    ).count()
    new_contacts = ContactRequest.objects.filter(status=ContactRequest.Status.NEW).count()
    pending_job_applications = JobApplication.objects.filter(status="PENDING").count()

    alerts = []
    if reservations_by_status["pending"]:
        alerts.append({
            "icon": "fa-calendar-check", "color": "warning",
            "text": f"{_plural(reservations_by_status['pending'], 'réservation')} en attente de confirmation",
            "link": reverse("dashboard:reservations_list") + "?status=PENDING",
        })
    if new_contacts:
        alerts.append({
            "icon": "fa-envelope-open-text", "color": "danger",
            "text": f"{_plural(new_contacts, 'nouvelle demande', 'nouvelles demandes')} de contact / devis",
            "link": reverse("dashboard:contacts_list") + "?status=NEW",
        })
    if pending_applications:
        alerts.append({
            "icon": "fa-user-plus", "color": "info",
            "text": f"{_plural(pending_applications, 'candidature')} partenaire à examiner",
            "link": reverse("dashboard:partner_applications_list") + "?status=pending",
        })
    if pending_contracts:
        alerts.append({
            "icon": "fa-file-signature", "color": "primary",
            "text": f"{_plural(pending_contracts, 'contrat')} à valider",
            "link": reverse("dashboard:partner_contracts_list") + "?status=pending",
        })
    if unread_messages:
        alerts.append({
            "icon": "fa-comments", "color": "success",
            "text": f"{_plural(unread_messages, 'message')} non lu{'s' if unread_messages > 1 else ''}",
            "link": reverse("messaging:admin_conversations_list"),
        })
    if equipment_stats["maintenance"]:
        alerts.append({
            "icon": "fa-screwdriver-wrench", "color": "danger",
            "text": f"{_plural(equipment_stats['maintenance'], 'équipement')} en maintenance",
            "link": reverse("dashboard:equipments_list") + "?status=MAINTENANCE",
        })
    if pending_job_applications:
        alerts.append({
            "icon": "fa-briefcase", "color": "info",
            "text": f"{_plural(pending_job_applications, 'candidature')} emploi / stage à traiter",
            "link": reverse("services_app:admin_jobs_list"),
        })

    # Taux d'occupation : heures réservées (confirmées) / heures ouvrables (8 h par jour et par studio)
    total_studios = Studio.objects.filter(is_active=True).count()
    occupation_rate = 0
    if start_date and total_studios:
        booked_hours = sum(
            (min(r.end_datetime, end_date) - max(r.start_datetime, start_date)).total_seconds() / 3600
            for r in Reservation.objects.filter(
                status__in=[ReservationStatus.CONFIRMED, ReservationStatus.COMPLETED],
                studio__isnull=False, start_datetime__lt=end_date, end_datetime__gt=start_date,
            ).only("start_datetime", "end_datetime")
        )
        days = max((end_date - start_date).total_seconds() / 86400, 1 / 3)
        occupation_rate = min(booked_hours / (total_studios * days * 8) * 100, 100)

    context = {
        "current_period": period,
        "total_revenue": total_revenue,
        "recent_revenue": recent_revenue,
        "total_reservations": reservations_qs.count(),
        "total_clients": User.objects.filter(role=User.Role.CLIENT, is_staff=False).count(),
        "total_employees": User.objects.filter(is_employee=True, is_active=True).count(),
        "equipments_available": equipment_stats["available"],
        "equipments_maintenance": equipment_stats["maintenance"],
        "total_equipments": equipment_stats["total"],
        "active_services": Service.objects.filter(is_active=True).count(),
        "active_trainings": Training.objects.filter(is_active=True).count(),
        "active_partners": Partner.objects.filter(active=True).count(),
        "total_business_partners": bp_stats["active"],
        "pending_applications": pending_applications,
        "pending_contracts": pending_contracts,
        "total_commission_earned": total_commission_earned,
        "total_commission_paid": total_commission_paid,
        "pending_commission": total_commission_earned - total_commission_paid,
        "reservations_by_status": reservations_by_status,
        "top_studios": Reservation.objects.filter(studio__isnull=False)
            .values("studio__name").annotate(count=Count("id")).order_by("-count")[:5],
        "top_services": Reservation.objects.filter(service__isnull=False)
            .values("service__name").annotate(count=Count("id")).order_by("-count")[:5],
        "top_partners": BusinessPartner.objects.filter(is_active=True).select_related("user")
            .order_by("-total_revenue")[:5],
        "revenue_chart_data": revenue_chart_data,
        "alerts": alerts,
        "last_reservations": Reservation.objects.select_related("user", "studio", "service")
            .order_by("-created_at")[:8],
        "latest_contacts": ContactRequest.objects.order_by("-created_at")[:5],
        "upcoming_trainings": Training.objects.filter(is_active=True, start_date__gte=now.date())
            .order_by("start_date")[:5],
        "open_job_offers": JobOffer.objects.filter(status="PUBLISHED")
            .filter(Q(deadline__isnull=True) | Q(deadline__gte=now.date())).count(),
        "total_studios": total_studios,
        "occupation_rate": round(occupation_rate, 1),
        "new_contacts": new_contacts,
    }
    return render(request, "admin/dashboard.html", context)
