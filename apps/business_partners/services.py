from django.contrib.auth import get_user_model
from django.utils.text import slugify
from .models import BusinessPartner, PartnerApplication, Region
import random
import string

User = get_user_model()


def generate_partner_code(city_name):
    """Génère un code partenaire unique : BF-CITY-XXX"""
    city_code = slugify(city_name)[:4].upper()
    
    # Compter les partenaires existants dans cette ville
    count = BusinessPartner.objects.filter(
        partner_code__startswith=f'BF-{city_code}'
    ).count() + 1
    
    return f"BF-{city_code}-{count:03d}"


def activate_partner(application, admin_user):
    """
    Active un partenaire après approbation de sa candidature
    Crée un compte utilisateur et un profil BusinessPartner
    """
    # Vérifier si déjà activé
    if hasattr(application, 'partner_profile'):
        return application.partner_profile
    
    # Générer un nom d'utilisateur unique
    username = slugify(application.full_name)
    if User.objects.filter(username=username).exists():
        username = f"{username}_{random.randint(1000, 9999)}"
    
    # Créer l'utilisateur
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    user = User.objects.create_user(
        username=username,
        email=application.email,
        password=password,
        first_name=application.full_name.split()[0],
        last_name=' '.join(application.full_name.split()[1:]) if len(application.full_name.split()) > 1 else '',
    )
    
    # Créer le profil partenaire
    partner_code = generate_partner_code(application.city.name)
    
    partner = BusinessPartner.objects.create(
        application=application,
        user=user,
        partner_code=partner_code,
        commission_rate=20.00,  # Par défaut
        is_active=True
    )
    
    # Mettre à jour le statut de la candidature
    application.status = 'approved'
    application.reviewed_by = admin_user
    application.reviewed_at = timezone.now()
    application.save()
    
    # Envoyer les identifiants par email
    from apps.notifications.emailing import send_partner_activation_email
    send_partner_activation_email(partner, password)
    
    return partner


def calculate_partner_performance(partner):
    """Calcule les performances d'un partenaire"""
    from django.db.models import Sum, Avg, Count
    from .models import Contract
    
    contracts = Contract.objects.filter(partner=partner)
    
    stats = contracts.aggregate(
        total_contracts=Count('id'),
        total_amount=Sum('contract_amount'),
        total_commission=Sum('commission_amount'),
        avg_contract_value=Avg('contract_amount'),
        completed=Count('id', filter=Q(status='completed')),
        pending=Count('id', filter=Q(status='pending')),
    )
    
    return stats


def get_top_partners(limit=10):
    """Retourne les meilleurs partenaires par CA généré"""
    return BusinessPartner.objects.filter(
        is_active=True
    ).order_by('-total_revenue')[:limit]