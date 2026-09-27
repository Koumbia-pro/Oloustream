"""Limitation simple du nombre de tentatives (connexion, formulaires publics)."""
from django.core.cache import cache


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


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
