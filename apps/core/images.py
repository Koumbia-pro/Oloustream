"""
Optimisation automatique des photos envoyées sur le site.

Chaque photo publique (studios, matériel, formations, logos, témoignages, avatars…) est,
au moment de l'enregistrement :
- redressée selon son orientation EXIF (photos de téléphone) ;
- réduite à 1600 px de côté au maximum ;
- convertie en WebP (beaucoup plus léger que JPG/PNG, transparence conservée).

Une photo de 3 Mo passe ainsi généralement sous les 250 Ko, sans perte visible.
Les fichiers privés (CV, pièces d'identité, contrats) ne sont jamais touchés.
"""
import io
import logging
from pathlib import Path

from django.apps import apps
from django.core.files.base import ContentFile
from django.db.models.signals import pre_save
from PIL import Image, ImageOps, UnidentifiedImageError

logger = logging.getLogger(__name__)

MAX_SIDE = 1600
WEBP_QUALITY = 82

# (modèle, champ) des photos publiques à optimiser
OPTIMIZED_IMAGE_FIELDS = [
    ("accounts.User", "avatar"),
    ("core.Testimonial", "photo"),
    ("studio.Studio", "image"),
    ("studio.Equipment", "photo"),
    ("services_app.Partner", "logo"),
    ("services_app.Service", "image"),
    ("services_app.Training", "image"),
    ("services_app.JobOffer", "poster"),
]


def optimize_image_bytes(data, max_side=MAX_SIDE, quality=WEBP_QUALITY):
    """
    Retourne les octets WebP optimisés, ou None si l'image doit rester telle quelle
    (format non reconnu, GIF animé, ou résultat pas plus léger que l'original).
    """
    try:
        with Image.open(io.BytesIO(data)) as source:
            if getattr(source, "is_animated", False):
                return None
            image = ImageOps.exif_transpose(source)
            has_alpha = image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info)
            image = image.convert("RGBA" if has_alpha else "RGB")
            image.thumbnail((max_side, max_side), Image.LANCZOS)
            buffer = io.BytesIO()
            image.save(buffer, "WEBP", quality=quality, method=6)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        logger.warning("Image non optimisée : %s", exc)
        return None
    result = buffer.getvalue()
    return result if len(result) < len(data) else None


def optimize_field_file(field_file):
    """Remplace en mémoire un fichier fraîchement envoyé par sa version optimisée."""
    if not field_file or getattr(field_file, "_committed", True):
        return False  # pas de nouveau fichier envoyé
    upload = field_file.file
    upload.seek(0)
    optimized = optimize_image_bytes(upload.read())
    upload.seek(0)
    if optimized is None:
        return False
    new_name = f"{Path(field_file.name).stem}.webp"
    field_file.file = ContentFile(optimized, name=new_name)
    field_file.name = new_name
    field_file._committed = False
    return True


def _make_receiver(field_name):
    def receiver(sender, instance, **kwargs):
        optimize_field_file(getattr(instance, field_name))
    return receiver


_receivers = []  # références conservées : les signaux ne gardent que des références faibles


def connect_image_optimization():
    for label, field_name in OPTIMIZED_IMAGE_FIELDS:
        model = apps.get_model(label)
        receiver = _make_receiver(field_name)
        _receivers.append(receiver)
        pre_save.connect(receiver, sender=model, dispatch_uid=f"optimize-image-{label}-{field_name}")
