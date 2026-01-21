# apps/studio/admin.py

from django.contrib import admin

from .models import (
    Studio,
    EquipmentCategory,
    Equipment,
    EquipmentUsageHistory,
    Reservation,
    ReservationStatusHistory,
)
from .forms import ReservationAdminForm, EquipmentForm


@admin.register(Studio)
class StudioAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "country", "price_per_hour", "status", "is_active")
    list_filter = ("status", "studio_type", "is_active")
    search_fields = ("name", "code", "address", "city", "country")
    ordering = ("name",)


@admin.register(EquipmentCategory)
class EquipmentCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "short_description")
    search_fields = ("name",)

    def short_description(self, obj):
        if obj.description:
            return (obj.description[:50] + "…") if len(obj.description) > 50 else obj.description
        return ""
    short_description.short_description = "Description"


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    form = EquipmentForm
    list_display = (
        "name",
        "category",
        "brand",
        "model",
        "status",
        "is_available_for_rent",
        "location",
    )
    list_filter = ("category", "status", "is_available_for_rent")
    search_fields = ("name", "brand", "model", "serial_number")
    readonly_fields = ("created_at",)
    fieldsets = (
        ("Informations de base", {
            "fields": (
                "name",
                "brand",
                "model",
                "category",
                "serial_number",
            )
        }),
        ("Achat", {
            "fields": (
                "purchase_date",
                "purchase_price",
            ),
            "classes": ("collapse",),
        }),
        ("État & disponibilité", {
            "fields": (
                "status",
                "is_available_for_rent",
                "current_user",
                "location",
            )
        }),
        ("Spécifications & notes", {
            "fields": (
                "technical_specs",
                "accessories_included",
                "important_notes",
            ),
            "classes": ("collapse",),
        }),
        ("Maintenance", {
            "fields": (
                "last_maintenance_date",
                "next_maintenance_date",
                "maintenance_notes",
            ),
            "classes": ("collapse",),
        }),
        ("Documents & images", {
            "fields": (
                "photo",
                "manual",
            ),
            "classes": ("collapse",),
        }),
        ("Métadonnées", {
            "fields": ("created_at",),
        }),
    )


@admin.register(EquipmentUsageHistory)
class EquipmentUsageHistoryAdmin(admin.ModelAdmin):
    list_display = ("equipment", "start_datetime", "end_datetime", "used_by")
    list_filter = ("equipment", "used_by")
    search_fields = ("equipment__name", "used_by__username")
    date_hierarchy = "start_datetime"


class ReservationStatusHistoryInline(admin.TabularInline):
    model = ReservationStatusHistory
    extra = 0
    readonly_fields = ("old_status", "new_status", "changed_by", "changed_at", "note")


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    form = ReservationAdminForm
    list_display = (
        "id",
        "user",
        "studio",
        "start_datetime",
        "end_datetime",
        "status",
        "created_at",
    )
    list_filter = ("status", "studio", "service")
    search_fields = ("user__username", "user__email", "studio__name")
    date_hierarchy = "start_datetime"
    inlines = [ReservationStatusHistoryInline]


@admin.register(ReservationStatusHistory)
class ReservationStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("reservation", "old_status", "new_status", "changed_by", "changed_at")
    list_filter = ("old_status", "new_status")
    search_fields = ("reservation__id", "changed_by__username")
    date_hierarchy = "changed_at"



