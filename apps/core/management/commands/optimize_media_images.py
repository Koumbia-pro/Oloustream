"""
Compresse les photos déjà en ligne (studios, matériel, formations, logos…) en WebP 1600 px max.

    python manage.py optimize_media_images              # simulation : affiche le gain sans rien changer
    python manage.py optimize_media_images --appliquer  # applique

Les anciens fichiers ne sont pas supprimés (sécurité) : ils restent dans media/ et pourront
être effacés plus tard. Les fichiers privés (CV, contrats, pièces d'identité) ne sont pas concernés.
"""
from pathlib import Path

from django.apps import apps
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from apps.core.images import OPTIMIZED_IMAGE_FIELDS, optimize_image_bytes


class Command(BaseCommand):
    help = "Compresse en WebP les photos publiques déjà envoyées sur le site."

    def add_arguments(self, parser):
        parser.add_argument("--appliquer", action="store_true", help="Applique les changements (sinon simulation).")

    def handle(self, *args, appliquer=False, **options):
        before_total = after_total = changed = 0
        for label, field_name in OPTIMIZED_IMAGE_FIELDS:
            model = apps.get_model(label)
            for obj in model.objects.exclude(**{field_name: ""}).exclude(**{f"{field_name}__isnull": True}):
                field_file = getattr(obj, field_name)
                if field_file.name.lower().endswith(".webp"):
                    continue
                try:
                    with field_file.open("rb") as handle:
                        data = handle.read()
                except (FileNotFoundError, OSError):
                    self.stdout.write(self.style.WARNING(f"  introuvable : {field_file.name}"))
                    continue
                optimized = optimize_image_bytes(data)
                if optimized is None:
                    continue
                before_total += len(data)
                after_total += len(optimized)
                changed += 1
                self.stdout.write(f"  {label}.{field_name} #{obj.pk} : {field_file.name} "
                                  f"{len(data) // 1024} Ko -> {len(optimized) // 1024} Ko")
                if appliquer:
                    field_file.save(f"{Path(field_file.name).stem}.webp", ContentFile(optimized), save=False)
                    model.objects.filter(pk=obj.pk).update(**{field_name: field_file.name})

        mode = "appliqué" if appliquer else "SIMULATION (ajoutez --appliquer pour enregistrer)"
        self.stdout.write(self.style.SUCCESS(
            f"{changed} photo(s) : {before_total // 1024} Ko -> {after_total // 1024} Ko — {mode}"
        ))
