from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.http import HttpResponseRedirect
from .models import (
    Region, PartnerApplication, BusinessPartner, 
    Contract, CommissionPayment
)
from .services import activate_partner


# ============== CONFIGURATION DU SITE ADMIN ==============
admin.site.site_header = "Oloustream Administration"
admin.site.site_title = "Oloustream Admin"
admin.site.index_title = "Tableau de bord"


# ============== RÉGION ADMIN ==============
@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_priority_badge', 'active', 'partners_count']
    list_filter = ['is_priority', 'active']
    search_fields = ['name']
    list_editable = ['active']
    ordering = ['-is_priority', 'name']
    
    def is_priority_badge(self, obj):
        if obj.is_priority:
            return format_html('<span style="color: #dc3545;">⭐ Prioritaire</span>')
        return '-'
    is_priority_badge.short_description = 'Type'
    
    def partners_count(self, obj):
        count = obj.partnerapplication_set.filter(status='approved').count()
        if count > 0:
            return format_html('<strong style="color: green;">{}</strong>', count)
        return '0'
    partners_count.short_description = 'Partenaires actifs'


# ============== CANDIDATURES PARTENAIRES ADMIN ==============
@admin.register(PartnerApplication)
class PartnerApplicationAdmin(admin.ModelAdmin):
    # Configuration de la liste
    list_display = [
        'id', 'full_name', 'city_display', 'phone', 
        'status_badge', 'network_badge', 'created_at_formatted', 
        'action_buttons'
    ]
    list_filter = [
        'status', 'city', 'network_strength', 
        'availability', 'created_at'
    ]
    search_fields = [
        'full_name', 'phone', 'email', 'whatsapp', 
        'id_number', 'current_activity'
    ]
    ordering = ['-created_at']
    list_per_page = 25
    
    # Configuration du détail
    readonly_fields = [
        'created_at', 'updated_at', 'reviewed_at', 
        'reviewed_by', 'formatted_id_display'
    ]
    
    fieldsets = (
        ('🔍 Informations de suivi', {
            'fields': ('status', 'internal_notes'),
            'classes': ('wide',)
        }),
        ('👤 Informations personnelles', {
            'fields': (
                'full_name', 'phone', 'email', 'whatsapp',
                'formatted_id_display', 'id_document'
            )
        }),
        ('📍 Localisation', {
            'fields': ('city', 'address')
        }),
        ('💼 Profil professionnel', {
            'fields': (
                'current_activity', 'experience_years',
                'network_strength', 'network_description',
                'sectors_knowledge', 'availability'
            )
        }),
        ('💡 Motivations', {
            'fields': ('why_oloustream', 'references')
        }),
        ('📅 Métadonnées', {
            'fields': ('created_at', 'updated_at', 'reviewed_at', 'reviewed_by'),
            'classes': ('collapse',)
        }),
    )
    
    # URLs personnalisées
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:pk>/approve/',
                self.admin_site.admin_view(self.approve_view),
                name='business_partners_partnerapplication_approve',
            ),
            path(
                '<int:pk>/reject/',
                self.admin_site.admin_view(self.reject_view),
                name='business_partners_partnerapplication_reject',
            ),
        ]
        return custom_urls + urls
    
    # Méthodes d'affichage personnalisées
    def city_display(self, obj):
        if obj.city and obj.city.is_priority:
            return format_html(
                '<strong>{} ⭐</strong>', 
                obj.city.name
            )
        return obj.city.name if obj.city else '-'
    city_display.short_description = 'Ville'
    
    def status_badge(self, obj):
        colors = {
            'pending': ('warning', '⏳'),
            'reviewing': ('info', '🔍'),
            'interview': ('primary', '📞'),
            'approved': ('success', '✅'),
            'rejected': ('danger', '❌'),
        }
        color_class, icon = colors.get(obj.status, ('secondary', '❓'))
        
        return format_html(
            '<span class="badge bg-{}" style="font-size: 12px;">'
            '{} {}</span>',
            color_class,
            icon,
            obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    
    def network_badge(self, obj):
        strengths = {
            'weak': ('🔴', '#dc3545'),
            'medium': ('🟡', '#ffc107'),
            'strong': ('🟢', '#28a745'),
            'very_strong': ('⭐', '#007bff'),
        }
        icon, color = strengths.get(obj.network_strength, ('❓', '#6c757d'))
        
        return format_html(
            '<span style="color: {}; font-size: 16px;">{}</span> {}',
            color, icon, obj.get_network_strength_display()
        )
    network_badge.short_description = 'Réseau'
    
    def created_at_formatted(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M')
    created_at_formatted.short_description = 'Date candidature'
    
    def formatted_id_display(self, obj):
        return format_html(
            '<strong>Type :</strong> {}<br>'
            '<strong>Numéro :</strong> {}',
            obj.get_id_type_display(),
            obj.id_number
        )
    formatted_id_display.short_description = 'Pièce d\'identité'
    
    def action_buttons(self, obj):
        """Boutons d'action dans la liste"""
        if obj.status in ['pending', 'reviewing']:
            approve_url = reverse(
                'admin:business_partners_partnerapplication_approve', 
                args=[obj.pk]
            )
            reject_url = reverse(
                'admin:business_partners_partnerapplication_reject', 
                args=[obj.pk]
            )
            
            return format_html(
                '<div style="min-width: 200px;">'
                '<a class="button" style="background: #28a745; color: white; '
                'padding: 5px 10px; border-radius: 3px; text-decoration: none; '
                'margin-right: 5px; display: inline-block;" '
                'href="{}" onclick="return confirm(\'Confirmer l\\\'approbation ?\');">'
                '✅ Approuver</a>'
                '<a class="button" style="background: #dc3545; color: white; '
                'padding: 5px 10px; border-radius: 3px; text-decoration: none; '
                'display: inline-block;" '
                'href="{}" onclick="return confirm(\'Confirmer le rejet ?\');">'
                '❌ Rejeter</a>'
                '</div>',
                approve_url,
                reject_url
            )
        
        elif obj.status == 'approved' and hasattr(obj, 'partner_profile'):
            partner_url = reverse(
                'admin:business_partners_businesspartner_change', 
                args=[obj.partner_profile.pk]
            )
            return format_html(
                '<a class="button" style="background: #007bff; color: white; '
                'padding: 5px 10px; border-radius: 3px; text-decoration: none;" '
                'href="{}">👤 Voir partenaire</a>',
                partner_url
            )
        
        elif obj.status == 'approved':
            return format_html(
                '<span style="color: red;">⚠️ Erreur activation</span>'
            )
        
        elif obj.status == 'rejected':
            return format_html(
                '<span style="color: #6c757d;">Rejetée</span>'
            )
        
        return '-'
    action_buttons.short_description = 'Actions'
    
    # Vues personnalisées
    def approve_view(self, request, pk):
        """Vue pour approuver une candidature"""
        application = get_object_or_404(PartnerApplication, pk=pk)
        
        if application.status == 'approved':
            messages.warning(request, "⚠️ Cette candidature est déjà approuvée.")
        else:
            try:
                # Activer le partenaire
                partner = activate_partner(application, request.user)
                
                messages.success(
                    request,
                    format_html(
                        '✅ Partenaire activé avec succès !<br>'
                        'Code partenaire : <strong>{}</strong><br>'
                        'Un email avec les identifiants a été envoyé à {}',
                        partner.partner_code,
                        partner.user.email
                    )
                )
                
                # Rediriger vers le détail du partenaire
                partner_url = reverse(
                    'admin:business_partners_businesspartner_change',
                    args=[partner.pk]
                )
                return HttpResponseRedirect(partner_url)
                
            except Exception as e:
                messages.error(
                    request, 
                    f"❌ Erreur lors de l'activation : {str(e)}"
                )
        
        return redirect('admin:business_partners_partnerapplication_changelist')
    
    def reject_view(self, request, pk):
        """Vue pour rejeter une candidature"""
        application = get_object_or_404(PartnerApplication, pk=pk)
        
        application.status = 'rejected'
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.internal_notes = f"Rejetée par {request.user} le {timezone.now().strftime('%d/%m/%Y %H:%M')}"
        application.save()
        
        messages.warning(
            request, 
            f"❌ Candidature de {application.full_name} rejetée."
        )
        
        return redirect('admin:business_partners_partnerapplication_changelist')
    
    # Actions en masse
    actions = ['mark_as_reviewing', 'mark_as_interview']
    
    @admin.action(description='Marquer comme "En cours d\'examen"')
    def mark_as_reviewing(self, request, queryset):
        updated = queryset.update(status='reviewing')
        messages.success(
            request,
            f"{updated} candidature(s) marquée(s) en cours d'examen."
        )
    
    @admin.action(description='Marquer comme "Entretien planifié"')
    def mark_as_interview(self, request, queryset):
        updated = queryset.update(status='interview')
        messages.info(
            request,
            f"{updated} candidature(s) marquée(s) pour entretien."
        )


# ============== PARTENAIRES ACTIFS ADMIN ==============
@admin.register(BusinessPartner)
class BusinessPartnerAdmin(admin.ModelAdmin):
    list_display = [
        'partner_code', 'full_name', 'city', 
        'total_contracts', 'total_revenue_formatted',
        'commission_earned_formatted', 'commission_paid_formatted',
        'pending_commission_formatted', 'is_active_badge',
        'last_activity'
    ]
    list_filter = ['is_active', 'activated_at', 'application__city']
    search_fields = [
        'partner_code', 'user__first_name', 
        'user__last_name', 'user__email'
    ]
    ordering = ['-total_revenue']
    readonly_fields = [
        'partner_code', 'user', 'application',
        'total_contracts', 'total_revenue',
        'total_commission_earned', 'total_commission_paid',
        'activated_at', 'last_contract_at'
    ]
    
    fieldsets = (
        ('🆔 Identification', {
            'fields': ('partner_code', 'user', 'application')
        }),
        ('⚙️ Configuration', {
            'fields': ('commission_rate', 'is_active', 'suspension_reason')
        }),
        ('📊 Performance', {
            'fields': (
                'total_contracts', 'total_revenue',
                'total_commission_earned', 'total_commission_paid'
            )
        }),
        ('📅 Dates', {
            'fields': ('activated_at', 'last_contract_at')
        }),
    )
    
    def full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    full_name.short_description = 'Nom'
    
    def city(self, obj):
        if obj.application.city:
            if obj.application.city.is_priority:
                return format_html(
                    '{} ⭐', 
                    obj.application.city.name
                )
            return obj.application.city.name
        return '-'
    city.short_description = 'Ville'
    
    def total_revenue_formatted(self, obj):
        return format_html(
            '<strong>{:,.0f}</strong> FCFA', 
            obj.total_revenue
        )
    total_revenue_formatted.short_description = 'CA généré'
    
    def commission_earned_formatted(self, obj):
        return format_html(
            '<span style="color: #28a745;">{:,.0f} FCFA</span>',
            obj.total_commission_earned
        )
    commission_earned_formatted.short_description = 'Com. totale'
    
    def commission_paid_formatted(self, obj):
        return format_html(
            '<span style="color: #007bff;">{:,.0f} FCFA</span>',
            obj.total_commission_paid
        )
    commission_paid_formatted.short_description = 'Com. payée'
    
    def pending_commission_formatted(self, obj):
        pending = obj.pending_commission
        if pending > 0:
            return format_html(
                '<strong style="color: #dc3545;">{:,.0f} FCFA</strong>',
                pending
            )
        return format_html(
            '<span style="color: #6c757d;">0 FCFA</span>'
        )
    pending_commission_formatted.short_description = 'En attente'
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span class="badge bg-success">✅ Actif</span>'
            )
        return format_html(
            '<span class="badge bg-danger">❌ Suspendu</span>'
        )
    is_active_badge.short_description = 'Statut'
    
    def last_activity(self, obj):
        if obj.last_contract_at:
            days_ago = (timezone.now() - obj.last_contract_at).days
            if days_ago == 0:
                return format_html(
                    '<span style="color: green;">Aujourd\'hui</span>'
                )
            elif days_ago == 1:
                return format_html(
                    '<span style="color: green;">Hier</span>'
                )
            elif days_ago < 7:
                return format_html(
                    '<span style="color: orange;">Il y a {} jours</span>',
                    days_ago
                )
            else:
                return format_html(
                    '<span style="color: red;">Il y a {} jours</span>',
                    days_ago
                )
        return '-'
    last_activity.short_description = 'Dernière activité'
    
    # Actions
    actions = ['activate_partners', 'deactivate_partners']
    
    @admin.action(description='Activer les partenaires sélectionnés')
    def activate_partners(self, request, queryset):
        updated = queryset.update(is_active=True, suspension_reason='')
        messages.success(
            request,
            f"{updated} partenaire(s) activé(s)."
        )
    
    @admin.action(description='Suspendre les partenaires sélectionnés')
    def deactivate_partners(self, request, queryset):
        updated = queryset.update(
            is_active=False,
            suspension_reason=f'Suspendu par {request.user} le {timezone.now().strftime("%d/%m/%Y")}'
        )
        messages.warning(
            request,
            f"{updated} partenaire(s) suspendu(s)."
        )


# ============== CONTRATS ADMIN ==============
@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'partner_code', 'client_name_formatted',
        'service_type', 'amount_formatted',
        'commission_formatted', 'status_badge',
        'created_date', 'validation_button'
    ]
    list_filter = [
        'status', 'client_type', 'partner',
        'created_at', 'validated_at'
    ]
    search_fields = [
        'client_name', 'partner__partner_code',
        'service_type', 'description'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'commission_amount', 'created_at',
        'validated_at', 'validated_by', 'completed_at'
    ]
    
    fieldsets = (
        ('🤝 Partenaire', {
            'fields': ('partner',)
        }),
        ('👥 Client', {
            'fields': ('client_name', 'client_type', 'client_contact')
        }),
        ('📋 Projet', {
            'fields': ('service_type', 'description', 'contract_file')
        }),
        ('💰 Financier', {
            'fields': (
                'contract_amount', 'commission_rate', 'commission_amount'
            )
        }),
        ('📊 Statut & Validation', {
            'fields': (
                'status', 'validated_at', 'validated_by', 'completed_at'
            )
        }),
    )
    
    def partner_code(self, obj):
        return format_html(
            '<strong>{}</strong>',
            obj.partner.partner_code
        )
    partner_code.short_description = 'Partenaire'
    
    def client_name_formatted(self, obj):
        return format_html(
            '<strong>{}</strong><br>'
            '<small style="color: #6c757d;">{}</small>',
            obj.client_name,
            obj.get_client_type_display()
        )
    client_name_formatted.short_description = 'Client'
    
    def amount_formatted(self, obj):
        return format_html(
            '<strong>{:,.0f}</strong> FCFA',
            obj.contract_amount
        )
    amount_formatted.short_description = 'Montant'
    
    def commission_formatted(self, obj):
        return format_html(
            '<span style="color: #28a745;">'
            '<strong>{:,.0f}</strong> FCFA<br>'
            '<small>({}%)</small></span>',
            obj.commission_amount,
            obj.commission_rate
        )
    commission_formatted.short_description = 'Commission'
    
    def status_badge(self, obj):
        badges = {
            'draft': ('secondary', '📝 Brouillon'),
            'pending': ('warning', '⏳ En attente'),
            'validated': ('success', '✅ Validé'),
            'signed': ('info', '🖊️ Signé'),
            'in_progress': ('primary', '🔄 En cours'),
            'completed': ('success', '✔️ Terminé'),
            'cancelled': ('danger', '❌ Annulé'),
        }
        badge_class, label = badges.get(obj.status, ('secondary', obj.get_status_display()))
        
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            badge_class,
            label
        )
    status_badge.short_description = 'Statut'
    
    def created_date(self, obj):
        return obj.created_at.strftime('%d/%m/%Y')
    created_date.short_description = 'Date'
    
    def validation_button(self, obj):
        if obj.status == 'pending':
            return format_html(
                '<button class="btn btn-sm btn-success" '
                'onclick="if(confirm(\'Valider ce contrat ?\')) '
                'window.location.href=\'/admin/business_partners/contract/{}/change/\';">'
                '✅ Valider</button>',
                obj.pk
            )
        return '-'
    validation_button.short_description = 'Action'
    
    # Actions
    actions = ['validate_contracts', 'cancel_contracts']
    
    @admin.action(description='Valider les contrats sélectionnés')
    def validate_contracts(self, request, queryset):
        pending_contracts = queryset.filter(status='pending')
        
        for contract in pending_contracts:
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
        
        messages.success(
            request,
            f"{pending_contracts.count()} contrat(s) validé(s)."
        )
    
    @admin.action(description='Annuler les contrats sélectionnés')
    def cancel_contracts(self, request, queryset):
        updated = queryset.update(status='cancelled')
        messages.warning(
            request,
            f"{updated} contrat(s) annulé(s)."
        )


# ============== PAIEMENTS COMMISSIONS ADMIN ==============
@admin.register(CommissionPayment)
class CommissionPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'partner_formatted', 'amount_formatted',
        'method_badge', 'reference', 'date_formatted',
        'receipt_link'
    ]
    list_filter = ['payment_method', 'paid_at', 'partner']
    search_fields = ['partner__partner_code', 'reference']
    filter_horizontal = ['contracts']
    readonly_fields = ['paid_at', 'created_by']
    
    fieldsets = (
        ('🤝 Partenaire', {
            'fields': ('partner',)
        }),
        ('💰 Paiement', {
            'fields': (
                'amount', 'payment_method',
                'reference', 'receipt'
            )
        }),
        ('📋 Contrats concernés', {
            'fields': ('contracts',),
            'classes': ('collapse',)
        }),
        ('📝 Informations', {
            'fields': ('notes', 'paid_at', 'created_by')
        }),
    )
    
    def partner_formatted(self, obj):
        return format_html(
            '<strong>{}</strong><br>'
            '<small>{}</small>',
            obj.partner.partner_code,
            obj.partner.user.get_full_name()
        )
    partner_formatted.short_description = 'Partenaire'
    
    def amount_formatted(self, obj):
        return format_html(
            '<strong style="color: #28a745;">{:,.0f} FCFA</strong>',
            obj.amount
        )
    amount_formatted.short_description = 'Montant'
    
    def method_badge(self, obj):
        methods = {
            'orange_money': ('warning', '📱 Orange'),
            'bank_transfer': ('info', '🏦 Virement'),
            'check': ('secondary', '📄 Chèque'),
            'cash': ('success', '💵 Espèces'),
        }
        badge_class, label = methods.get(
            obj.payment_method,
            ('secondary', obj.get_payment_method_display())
        )
        
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            badge_class,
            label
        )
    method_badge.short_description = 'Méthode'
    
    def date_formatted(self, obj):
        return obj.paid_at.strftime('%d/%m/%Y %H:%M')
    date_formatted.short_description = 'Date paiement'
    
    def receipt_link(self, obj):
        if obj.receipt:
            return format_html(
                '<a href="{}" target="_blank">📄 Voir</a>',
                obj.receipt.url
            )
        return '-'
    receipt_link.short_description = 'Reçu'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)