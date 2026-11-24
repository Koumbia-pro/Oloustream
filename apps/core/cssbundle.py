"""
Regroupement des feuilles de style : une seule requête CSS par page au lieu de 2 ou 3.

Les fichiers sources restent séparés (on les modifie normalement). Après une modification :

    python manage.py build_css

Un test automatique vérifie que les fichiers regroupés sont à jour : sinon la mise en ligne est bloquée.
"""
from pathlib import Path

from django.conf import settings

STATIC_DIR = Path(settings.BASE_DIR) / "static"

BUNDLES = {
    "css/bundle-site.css": ["css/oloustream.css", "css/site.css", "css/theme-light.css"],
    "css/bundle-dashboard.css": ["css/oloustream.css", "css/dashboard.css"],
}


def build_bundle(bundle):
    sources = BUNDLES[bundle]
    parts = [
        "/* FICHIER GÉNÉRÉ — ne pas modifier directement.\n"
        f"   Sources : {', '.join(sources)}\n"
        "   Après une modification des sources : python manage.py build_css */\n"
    ]
    for source in sources:
        content = (STATIC_DIR / source).read_text(encoding="utf-8").rstrip() + "\n"
        parts.append(f"\n/* ===== {source} ===== */\n{content}")
    return "".join(parts)


def write_bundles():
    written = []
    for bundle in BUNDLES:
        path = STATIC_DIR / bundle
        content = build_bundle(bundle)
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8")
            written.append(bundle)
    return written
