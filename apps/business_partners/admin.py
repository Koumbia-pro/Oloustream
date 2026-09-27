from django.contrib import admin, messages
from django.db.models import Count, F, Q
from django.utils.html import format_html

from .models import BusinessPartner, CommissionPayment, Contract, PartnerApplication, Region
from .services import PartnerActionError, activate_partner, cancel_contract, validate_contract

admin.site.site_header = "Oloustream Administration"
admin.site.site_title = "Oloustream Admin"
admin.site.index_title = "Tableau de bord"


def fcfa(value):
    return f"{value or 0:,.0f} FCFA".replace(",", " ")


# ============== RÉGIONS ==============

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ["name", "is_priority", "active", "partners_count"]
    list_filter = ["is_priority", "active"]
    search_fields = ["name"]
    list_editable = ["is_priority", "active"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _partners=Count("partnerapplication", filter=Q(partnerapplication__status="approved"))
        )

    @admin.display(description="Partenaires actifs", ordering="_partners")
    def partners_count(self, obj):
        return obj._partners


# ============== CANDIDATURES ==============

@admin.register(PartnerApplication)
class PartnerApplicationAdmin(admin.ModelAdmin):
    list_display = ["id", "full_name", "city", "phone", "email", "status", "network_strength", "created_at"]
    list_filter = ["status", "city", "network_strength", "availability", "created_at"]
    search_fields = ["full_name", "phone", "email", "whatsapp", "id_number", "current_activity"]
    list_select_related = ["city"]
    readonly_fields = ["created_at", "updated_at", "reviewed_at", "reviewed_by"]
    date_hierarchy = "created_at"
    actions = ["approve_applications", "mark_as_reviewing", "mark_as_interview", "reject_applications"]
    fieldsets = (
        ("Identité", {"fields": ("full_name", "phone", "email", "whatsapp")}),
        ("Pièce d'identité", {"fields": ("id_type", "id_number", "id_document")}),
        ("Localisation", {"fields": ("city", "address")}),
        ("Profil", {"fields": ("current_activity", "experience_years", "network_strength",
                               "network_description", "sectors_knowledge", "why_oloustream",
                               "availability", "references")}),
        ("Suivi", {"fields": ("status", "internal_notes", "reviewed_by", "reviewed_at", "created_at", "updated_at")}),
    )

    @admin.action(description="Approuver et créer l'accès partenaire")
    def approve_applications(self, request, queryset):
        approved = 0
        for application in queryset.exclude(status="approved"):
            try:
                activate_partner(application, request.user)
                approved += 1
            except PartnerActionError as exc:
                self.message_user(request, f"{application.full_name} : {exc}", messages.ERROR)
        if approved:
            self.message_user(request, f"{approved} candidature(s) approuvée(s).", messages.SUCCESS)

    @admin.action(description="Marquer « en cours d'examen »")
    def mark_as_reviewing(self, request, queryset):
        updated = queryset.filter(status="pending").update(status="reviewing")
        self.message_user(request, f"{updated} candidature(s) mise(s) à jour.")

    @admin.action(description="Marquer « entretien planifié »")
    def mark_as_interview(self, request, queryset):
        updated = queryset.filter(status__in=["pending", "reviewing"]).update(status="interview")
        self.message_user(request, f"{updated} candidature(s) mise(s) à jour.")

    @admin.action(description="Rejeter")
    def reject_applications(self, request, queryset):
        from django.utils import timezone
        updated = queryset.exclude(status="approved").update(
            status="rejected", reviewed_by=request.user, reviewed_at=timezone.now()
        )
        self.message_user(request, f"{updated} candidature(s) rejetée(s).", messages.WARNING)


# ============== PARTENAIRES ==============

@admin.register(BusinessPartner)
class BusinessPartnerAdmin(admin.ModelAdmin):
    list_display = ["partner_code", "full_name", "city", "is_active", "total_contracts",
                    "revenue", "commission_earned", "commission_paid", "commission_pending"]
    list_filter = ["is_active", "application__city"]
    search_fields = ["partner_code", "user__first_name", "user__last_name", "user__email"]
    list_select_related = ["user", "application__city"]
    readonly_fields = ["partner_code", "total_contracts", "total_revenue", "total_commission_earned",
                       "total_commission_paid", "activated_at", "last_contract_at"]
    actions = ["activate_partners", "deactivate_partners"]

    @admin.display(description="Nom")
    def full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    @admin.display(description="Ville")
    def city(self, obj):
        return obj.application.city if obj.application_id else "-"

    @admin.display(description="CA généré", ordering="total_revenue")
    def revenue(self, obj):
        return fcfa(obj.total_revenue)

    @admin.display(description="Commission gagnée", ordering="total_commission_earned")
    def commission_earned(self, obj):
        return fcfa(obj.total_commission_earned)

    @admin.display(description="Commission versée", ordering="total_commission_paid")
    def commission_paid(self, obj):
        return fcfa(obj.total_commission_paid)

    @admin.display(description="À verser")
    def commission_pending(self, obj):
        pending = obj.pending_commission
        if pending > 0:
            return format_html('<strong style="color:#B45309">{}</strong>', fcfa(pending))
        return fcfa(pending)

    @admin.action(description="Réactiver")
    def activate_partners(self, request, queryset):
        updated = queryset.update(is_active=True, suspension_reason="")
        self.message_user(request, f"{updated} partenaire(s) réactivé(s).")

    @admin.action(description="Suspendre")
    def deactivate_partners(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} partenaire(s) suspendu(s).", messages.WARNING)


# ============== CONTRATS ==============

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ["id", "partner", "client_name", "client_type", "amount", "commission", "status", "created_at"]
    list_filter = ["status", "client_type", "created_at"]
    search_fields = ["client_name", "partner__partner_code", "service_type"]
    list_select_related = ["partner", "partner__user"]
    # Le statut se change via les actions (pour garder les statistiques cohérentes)
    readonly_fields = ["status", "commission_amount", "created_at", "validated_at", "validated_by", "completed_at"]
    date_hierarchy = "created_at"
    actions = ["validate_contracts", "cancel_contracts"]

    @admin.display(description="Montant", ordering="contract_amount")
    def amount(self, obj):
        return fcfa(obj.contract_amount)

    @admin.display(description="Commission", ordering="commission_amount")
    def commission(self, obj):
        return f"{fcfa(obj.commission_amount)} ({obj.commission_rate}%)"

    @admin.action(description="Valider les contrats en attente")
    def validate_contracts(self, request, queryset):
        count = 0
        for contract in queryset.filter(status="pending"):
            try:
                validate_contract(contract, request.user)
                count += 1
            except PartnerActionError as exc:
                self.message_user(request, f"Contrat #{contract.pk} : {exc}", messages.ERROR)
        self.message_user(request, f"{count} contrat(s) validé(s).", messages.SUCCESS)

    @admin.action(description="Annuler les contrats")
    def cancel_contracts(self, request, queryset):
        count = 0
        for contract in queryset:
            try:
                cancel_contract(contract, request.user)
                count += 1
            except PartnerActionError as exc:
                self.message_user(request, f"Contrat #{contract.pk} : {exc}", messages.ERROR)
        self.message_user(request, f"{count} contrat(s) annulé(s).", messages.WARNING)


# ============== PAIEMENTS DE COMMISSION ==============

@admin.register(CommissionPayment)
class CommissionPaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "partner", "amount_display", "payment_method", "reference", "paid_at"]
    list_filter = ["payment_method", "paid_at"]
    search_fields = ["partner__partner_code", "reference"]
    list_select_related = ["partner"]
    filter_horizontal = ["contracts"]
    readonly_fields = ["created_by"]

    @admin.display(description="Montant", ordering="amount")
    def amount_display(self, obj):
        return fcfa(obj.amount)

    def has_change_permission(self, request, obj=None):
        # Un paiement enregistré ne se modifie pas (sinon le total versé devient faux)
        return obj is None and super().has_change_permission(request, obj)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        if not change:
            BusinessPartner.objects.filter(pk=obj.partner_id).update(
                total_commission_paid=F("total_commission_paid") + obj.amount
            )
