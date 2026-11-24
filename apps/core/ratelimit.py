"""Limitation simple du nombre de tentatives (connexion, formulaires publics)."""
import ipaddress

from django.core.cache import cache


# Plages d'adresses de Cloudflare (https://www.cloudflare.com/ips/, relevées le 24/11/2026).
CLOUDFLARE_NETWORKS = [ipaddress.ip_network(n) for n in (
    "173.245.48.0/20", "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22", "141.101.64.0/18",
    "108.162.192.0/18", "190.93.240.0/20", "188.114.96.0/20", "197.234.240.0/22", "198.41.128.0/17",
    "162.158.0.0/15", "104.16.0.0/13", "104.24.0.0/14", "172.64.0.0/13", "131.0.72.0/22",
    "2400:cb00::/32", "2606:4700::/32", "2803:f800::/32", "2405:b500::/32", "2405:8100::/32",
    "2a06:98c0::/29", "2c0f:f248::/32",
)]


def _is_cloudflare(address):
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return any(ip in network for network in CLOUDFLARE_NETWORKS)


def client_ip(request):
    """
    Adresse IP réelle du visiteur.

    Le site est derrière Cloudflare : REMOTE_ADDR est alors l'adresse d'un serveur Cloudflare,
    partagée par de nombreux visiteurs. On lit l'en-tête CF-Connecting-IP uniquement quand la
    requête vient vraiment de Cloudflare ; sinon cet en-tête pourrait être falsifié par le client.
    """
    remote = request.META.get("REMOTE_ADDR", "")
    forwarded = request.META.get("HTTP_CF_CONNECTING_IP", "").strip()
    if forwarded and _is_cloudflare(remote):
        try:
            return str(ipaddress.ip_address(forwarded))
        except ValueError:
            pass
    return remote


class RateLimiter:
    def __init__(self, scope, limit, window_seconds):
        self.scope = scope
        self.limit = limit
        self.window = window_seconds

    def _key(self, identifier):
        return f"ratelimit:{self.scope}:{identifier}"

    def is_blocked(self, identifier):
        return cache.get(self._key(identifier), 0) >= self.limit

    def hit(self, identifier):
        key = self._key(identifier)
        if cache.add(key, 1, self.window):
            return 1
        try:
            return cache.incr(key)
        except ValueError:
            cache.set(key, 1, self.window)
            return 1

    def reset(self, identifier):
        cache.delete(self._key(identifier))
