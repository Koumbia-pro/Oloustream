from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, EmployeeProfile

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Oloustream', {'fields': ('role', 'avatar', 'phone', 'is_employee')}),
    )
    list_display = ('username', 'email', 'role', 'is_staff', 'is_employee')
    list_filter = ('role', 'is_employee', 'is_staff')

@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'position')
