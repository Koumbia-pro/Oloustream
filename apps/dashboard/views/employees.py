from django.contrib import messages
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.accounts.forms import EmployeeCreateForm, EmployeeUpdateForm
from apps.accounts.models import ContractTypeChoices, User
from apps.core.permissions import can_manage_user, team_admin_required
from apps.core.utils import excel_response, fmt_date, querystring_without_page

__all__ = [
    "employee_list_view", "employee_export_excel_view", "employee_detail_view", "employee_create_view",
    "employee_update_view", "employee_delete_view", "employee_change_password_view",
]

ROLE_EMPLOYEE_CHOICES = [c for c in User.Role.choices if c[0] != User.Role.CLIENT]


def _filtered_employees(request):
    qs = User.objects.filter(is_employee=True).select_related("employee_profile").order_by("last_name", "first_name")
    filters = {
        "q": request.GET.get("q", "").strip(),
        "role": request.GET.get("role", ""),
        "status": request.GET.get("status", ""),
        "contract_type": request.GET.get("contract_type", ""),
    }
    if filters["q"]:
        q = filters["q"]
        qs = qs.filter(
            Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
            | Q(email__icontains=q) | Q(phone__icontains=q)
            | Q(employee_profile__position__icontains=q) | Q(employee_profile__city__icontains=q)
        )
    if filters["role"]:
        qs = qs.filter(role=filters["role"])
    if filters["status"] == "active":
        qs = qs.filter(is_active=True)
    elif filters["status"] == "inactive":
        qs = qs.filter(is_active=False)
    if filters["contract_type"]:
        qs = qs.filter(employee_profile__contract_type=filters["contract_type"])
    return qs, filters


def _get_manageable_employee(request, user_id):
    employee = get_object_or_404(User.objects.select_related("employee_profile"), pk=user_id, is_employee=True)
    if not can_manage_user(request.user, employee):
        raise PermissionDenied("Vous ne pouvez pas modifier ce compte.")
    return employee


@team_admin_required
def employee_list_view(request):
    qs, filters = _filtered_employees(request)
    all_employees = User.objects.filter(is_employee=True)
    return render(request, "admin/employees/list.html", {
        "page_obj": Paginator(qs, 12).get_page(request.GET.get("page")),
        "q": filters["q"],
        "selected_role": filters["role"],
        "selected_status": filters["status"],
        "selected_contract_type": filters["contract_type"],
        "role_choices": ROLE_EMPLOYEE_CHOICES,
        "contract_type_choices": ContractTypeChoices.choices,
        "base_querystring": querystring_without_page(request),
        "total_count": all_employees.count(),
        "active_count": all_employees.filter(is_active=True).count(),
        "inactive_count": all_employees.filter(is_active=False).count(),
    })


@team_admin_required
def employee_export_excel_view(request):
    qs, _ = _filtered_employees(request)
    rows = []
    for e in qs:
        profile = getattr(e, "employee_profile", None)
        rows.append([
            e.id, e.username, e.last_name, e.first_name, e.email, e.phone, e.get_role_display(),
            "Actif" if e.is_active else "Inactif",
            fmt_date(profile.hire_date) if profile else "",
            profile.city if profile else "",
            profile.position if profile else "",
            profile.get_contract_type_display() if profile and profile.contract_type else "",
            float(profile.salary) if profile and profile.salary is not None else None,
        ])
    return excel_response(
        "employes", "Employés",
        ["ID", "Identifiant", "Nom", "Prénom", "Email", "Téléphone", "Rôle", "Statut",
         "Date d'embauche", "Ville", "Poste", "Type de contrat", "Salaire"],
        rows, [6, 18, 18, 18, 28, 16, 18, 10, 14, 16, 22, 16, 12],
    )


@team_admin_required
def employee_detail_view(request, user_id):
    employee = get_object_or_404(User.objects.select_related("employee_profile"), pk=user_id, is_employee=True)
    return render(request, "admin/employees/detail.html", {
        "employee": employee,
        "profile": getattr(employee, "employee_profile", None),
        "can_manage": can_manage_user(request.user, employee),
    })


@team_admin_required
def employee_create_view(request):
    if request.method == "POST":
        form = EmployeeCreateForm(request.POST, request.FILES, acting_user=request.user)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Employé « {user.get_full_name() or user.username} » créé avec succès.")
            return redirect("dashboard:employees_detail", user_id=user.pk)
    else:
        form = EmployeeCreateForm(acting_user=request.user)
    return render(request, "admin/employees/form.html", {"form": form})


@team_admin_required
def employee_update_view(request, user_id):
    employee = _get_manageable_employee(request, user_id)
    if request.method == "POST":
        form = EmployeeUpdateForm(request.POST, request.FILES, instance=employee, acting_user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Employé mis à jour avec succès.")
            return redirect("dashboard:employees_detail", user_id=employee.pk)
    else:
        form = EmployeeUpdateForm(instance=employee, acting_user=request.user)
    return render(request, "admin/employees/form.html", {"form": form, "employee": employee})


@team_admin_required
@require_http_methods(["GET", "POST"])
def employee_delete_view(request, user_id):
    employee = _get_manageable_employee(request, user_id)
    if employee.pk == request.user.pk:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect("dashboard:employees_detail", user_id=employee.pk)

    if request.method == "POST":
        name = employee.get_full_name() or employee.username
        employee.delete()
        messages.success(request, f"Employé « {name} » supprimé.")
        return redirect("dashboard:employees_list")
    return render(request, "admin/employees/confirm_delete.html", {"employee": employee})


@team_admin_required
def employee_change_password_view(request, user_id):
    employee = _get_manageable_employee(request, user_id)
    if request.method == "POST":
        form = AdminPasswordChangeForm(employee, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Mot de passe modifié avec succès.")
            return redirect("dashboard:employees_detail", user_id=employee.pk)
    else:
        form = AdminPasswordChangeForm(employee)
    for field in form.fields.values():
        field.widget.attrs.setdefault("class", "form-control")
    return render(request, "admin/employees/change_password.html", {"form": form, "employee": employee})
