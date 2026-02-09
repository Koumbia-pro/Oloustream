def site_settings(request):
    # On mettra la vraie config plus tard
    return {}


from apps.business_partners.models import PartnerApplication, Contract

def partner_counts(request):
    """Compteurs pour les partenaires dans le menu admin"""
    if request.user.is_authenticated and request.user.is_staff:
        return {
            'pending_applications_count': PartnerApplication.objects.filter(status='pending').count(),
            'pending_contracts_count': Contract.objects.filter(status='pending').count(),
        }
    return {}