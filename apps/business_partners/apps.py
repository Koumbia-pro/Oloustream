from django.apps import AppConfig


class BusinessPartnersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.business_partners'
    verbose_name = 'Partenaires d\'affaires'

    def ready(self):
        import apps.business_partners.signals  # Charger les signals
