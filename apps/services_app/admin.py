from django.contrib import admin
from .models import Partner, Service, Offer, Training, TrainingEnrollment, OfferApplication


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'active')
    list_filter = ('active',)
    search_fields = ('name',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'service', 'discount_percent', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'service')


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ('title', 'duration_hours', 'price', 'certification', 'is_active')
    list_filter = ('is_active', 'certification')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(TrainingEnrollment)
class TrainingEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'training', 'status', 'created_at')
    list_filter = ('status', 'training')
    search_fields = ('user__username', 'user__email')


@admin.register(OfferApplication)
class OfferApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'offer', 'status', 'created_at')
    list_filter = ('status', 'offer')
    search_fields = ('user__username', 'user__email', 'offer__title')