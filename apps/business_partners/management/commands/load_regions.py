from django.core.management.base import BaseCommand
from apps.business_partners.models import Region


class Command(BaseCommand):
    help = 'Charge les régions du Burkina Faso'

    def handle(self, *args, **kwargs):
        regions_data = [
            ('Bobo-Dioulasso', True),
            ('Koudougou', True),
            ('Fada N\'Gourma', True),
            ('Ouahigouya', True),
            ('Banfora', True),
            ('Dédougou', True),
            ('Tenkodogo', True),
            ('Ouagadougou', False),
            ('Kaya', False),
            ('Gaoua', False),
            ('Manga', False),
            ('Réo', False),
            ('Zorgo', False),
            ('Diapaga', False),
            ('Djibo', False),
        ]

        for name, is_priority in regions_data:
            region, created = Region.objects.get_or_create(
                name=name,
                defaults={'is_priority': is_priority}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Région créée : {name}')
                )
            else:
                self.stdout.write(f'⚠️  Région déjà existante : {name}')

        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 {len(regions_data)} régions chargées !')
        )