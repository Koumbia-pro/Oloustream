"""
En-tête Content-Security-Policy (CSP) : le navigateur n'exécute que les scripts
venant du site, des CDN listés ci-dessous, ou portant le « nonce » de la page.

Un script injecté par un pirate (faille XSS) est donc bloqué même s'il arrive
dans la page. Dans un gabarit, tout <script> écrit directement dans la page doit
porter : <script nonce="{{ csp_nonce }}">
"""
import secrets

CDN_SCRIPTS = "https://cdn.jsdelivr.net https://cdnjs.cloudflare.com"


def build_policy(nonce):
    return "; ".join([
        "default-src 'self'",
        f"script-src 'self' 'nonce-{nonce}' {CDN_SCRIPTS}",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com " + CDN_SCRIPTS,
        "font-src 'self' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com",
        "img-src 'self' data: blob: https://i.ytimg.com",
        "frame-src https://www.youtube-nocookie.com https://www.youtube.com",
        "connect-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ])


class ContentSecurityPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.csp_nonce = secrets.token_urlsafe(16)
        response = self.get_response(request)
        response.headers.setdefault("Content-Security-Policy", build_policy(request.csp_nonce))
        return response


def csp_nonce(request):
    """Processeur de contexte : {{ csp_nonce }} dans tous les gabarits."""
    return {"csp_nonce": getattr(request, "csp_nonce", "")}
