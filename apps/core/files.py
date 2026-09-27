"""
Téléchargement protégé des documents sensibles (pièces d'identité, CV, contrats, reçus).
Ces fichiers ne doivent jamais être liés directement via MEDIA_URL dans les gabarits :
utiliser {% url 'core:protected_file' kind obj.pk %}.
"""
import mimetypes
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404

from .permissions import is_team_admin


def _application_id(user, pk):
    from apps.business_partners.models import PartnerApplication
    obj = PartnerApplication.objects.get(pk=pk)
    return obj.id_document, user.is_staff


def _contract(user, pk):
    from apps.business_partners.models import Contract
    obj = Contract.objects.select_related("partner").get(pk=pk)
    return obj.contract_file, user.is_staff or obj.partner.user_id == user.id


def _receipt(user, pk):
    from apps.business_partners.models import CommissionPayment
    obj = CommissionPayment.objects.select_related("partner").get(pk=pk)
    return obj.receipt, user.is_staff or obj.partner.user_id == user.id


def _employee_contract(user, pk):
    from apps.accounts.models import EmployeeProfile
    obj = EmployeeProfile.objects.get(pk=pk)
    return obj.contract_document, is_team_admin(user) or obj.user_id == user.id


def _cv(user, pk):
    from apps.services_app.models import JobApplication
    obj = JobApplication.objects.get(pk=pk)
    return obj.cv, user.is_staff or obj.user_id == user.id


RESOLVERS = {
    "piece-identite": _application_id,
    "contrat-partenaire": _contract,
    "recu": _receipt,
    "contrat-employe": _employee_contract,
    "cv": _cv,
}


@login_required
def protected_file(request, kind, pk):
    resolver = RESOLVERS.get(kind)
    if resolver is None:
        raise Http404
    try:
        field_file, allowed = resolver(request.user, pk)
    except Exception:
        raise Http404
    if not allowed or not field_file:
        raise Http404
    try:
        handle = field_file.open("rb")
    except (FileNotFoundError, OSError):
        raise Http404("Fichier introuvable.")

    filename = Path(field_file.name).name
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    inline = content_type in {"application/pdf", "image/jpeg", "image/png", "image/webp", "image/gif"}
    response = FileResponse(handle, as_attachment=not inline, filename=filename, content_type=content_type)
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response
