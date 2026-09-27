from django.contrib import admin

from .models import ContactRequest


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "company", "subject", "email", "phone", "status", "created_at")
    list_filter = ("status", "subject", "created_at")
    search_fields = ("full_name", "company", "email", "phone", "message")
    list_editable = ("status",)
    readonly_fields = ("ip_address", "created_at")
    date_hierarchy = "created_at"
