"""Validateurs de fichiers envoyés par les utilisateurs."""
from pathlib import Path

from django.core.exceptions import ValidationError

MB = 1024 * 1024

DOCUMENT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
PDF_EXTENSIONS = {".pdf"}

# Signatures binaires ("magic numbers") pour vérifier le vrai contenu du fichier
_SIGNATURES = {
    ".pdf": [b"%PDF"],
    ".jpg": [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
    ".png": [b"\x89PNG\r\n\x1a\n"],
    ".gif": [b"GIF87a", b"GIF89a"],
    ".webp": [b"RIFF"],
}


def _check_file(f, allowed_extensions, max_size_mb):
    if not f:
        return f
    ext = Path(f.name).suffix.lower()
    if ext not in allowed_extensions:
        allowed = ", ".join(sorted(e.lstrip(".").upper() for e in allowed_extensions))
        raise ValidationError(f"Format non autorisé. Formats acceptés : {allowed}.")
    if f.size > max_size_mb * MB:
        raise ValidationError(f"Le fichier ne doit pas dépasser {max_size_mb} Mo.")

    signatures = _SIGNATURES.get(ext)
    if signatures and hasattr(f, "read"):
        position = f.tell() if hasattr(f, "tell") else 0
        f.seek(0)
        head = f.read(16)
        f.seek(position)
        if not any(head.startswith(sig) for sig in signatures):
            raise ValidationError("Le contenu du fichier ne correspond pas à son extension.")
    return f


def validate_document(f, max_size_mb=5):
    """PDF ou image (pièces d'identité, contrats, reçus)."""
    return _check_file(f, DOCUMENT_EXTENSIONS, max_size_mb)


def validate_image(f, max_size_mb=5):
    return _check_file(f, IMAGE_EXTENSIONS, max_size_mb)


def validate_pdf(f, max_size_mb=10):
    return _check_file(f, PDF_EXTENSIONS, max_size_mb)


class UploadValidationMixin:
    """
    Mixin de formulaire : valide automatiquement les champs fichiers listés.
    Exemple : upload_rules = {"cv": validate_pdf, "photo": validate_image}
    """
    upload_rules = {}

    def clean(self):
        cleaned_data = super().clean()
        for field_name, validator in self.upload_rules.items():
            uploaded = self.files.get(self.add_prefix(field_name))
            if uploaded:
                try:
                    validator(uploaded)
                except ValidationError as exc:
                    self.add_error(field_name, exc)
        return cleaned_data
