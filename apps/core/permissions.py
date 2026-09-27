"""Règles d'accès communes (équipe, administrateurs, partenaires)."""
from functools import wraps

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def is_team_admin(user):
    """
    Peut gérer l'équipe (employés, rôles, mots de passe) :
    super-utilisateur Django ou rôle Super Administrateur / Manager.
    """
    if not (user.is_authenticated and user.is_active):
        return False
    if user.is_superuser:
        return True
    role = getattr(user, "role", None)
    return user.is_staff and role in {"SUPERADMIN", "MANAGER"}


def can_manage_user(actor, target):
    """Un membre de l'équipe ne peut pas modifier un compte plus privilégié que le sien."""
    if actor.is_superuser:
        return True
    if target.is_superuser:
        return False
    if getattr(target, "role", None) == "SUPERADMIN" and getattr(actor, "role", None) != "SUPERADMIN":
        return False
    return is_team_admin(actor)


def team_admin_required(view_func):
    @staff_member_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_team_admin(request.user):
            raise PermissionDenied("Réservé aux administrateurs.")
        return view_func(request, *args, **kwargs)
    return wrapper


def partner_required(view_func):
    """Espace partenaire : utilisateur connecté, partenaire enregistré et actif."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        partner = getattr(request.user, "business_partner", None)
        if partner is None:
            messages.error(request, "Cet espace est réservé aux partenaires d'affaires Oloustream.")
            return redirect("partners:program_info")
        if not partner.is_active:
            messages.error(request, "Votre compte partenaire est suspendu. Contactez l'équipe Oloustream.")
            return redirect("core:home")
        request.partner = partner
        return view_func(request, *args, **kwargs)
    return wrapper
