"""
{% asset 'css/site.css' %} -> /static/css/site.css?v=<empreinte du contenu>

Les fichiers CSS/JS sont gardés 30 jours en cache (navigateurs et Cloudflare). L'empreinte change
dès que le contenu du fichier change : les visiteurs reçoivent donc toujours la dernière version,
sans avoir à modifier un numéro de version à la main.
"""
import hashlib
from functools import lru_cache

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@lru_cache(maxsize=None)
def _fingerprint(path):
    found = finders.find(path)
    if not found:
        return ""
    with open(found, "rb") as handle:
        return hashlib.md5(handle.read(), usedforsecurity=False).hexdigest()[:10]


@register.simple_tag
def asset(path):
    url = static(path)
    version = _fingerprint(path)
    return f"{url}?v={version}" if version else url
