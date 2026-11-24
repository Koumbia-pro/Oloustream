from django.core.management.base import BaseCommand

from apps.core.cssbundle import BUNDLES, write_bundles


class Command(BaseCommand):
    help = "Regroupe les feuilles de style (une seule requête CSS par page)."

    def handle(self, *args, **options):
        written = write_bundles()
        for bundle in BUNDLES:
            state = "mis à jour" if bundle in written else "déjà à jour"
            self.stdout.write(f"  static/{bundle} : {state}")
