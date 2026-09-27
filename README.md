# Oloustream

Site et plateforme de gestion d'Oloustream : studios, live streaming, production audiovisuelle,
location de matériel, formations, recrutement et programme de partenaires d'affaires.

Django 5 · Channels (chat) · MySQL en production (O2Switch) · SQLite en local.

## Organisation du code

| Dossier | Rôle |
|---|---|
| `oloustream/` | Configuration (settings, URLs, ASGI/WSGI) |
| `apps/core/` | Pages publiques, contact/devis, pages légales, utilitaires partagés (`utils`, `validators`, `permissions`, `ratelimit`, `files`) |
| `apps/accounts/` | Utilisateurs, connexion (limitée contre le brute-force), profil, employés |
| `apps/studio/` | Studios, matériel, réservations (contrôle des chevauchements dans `services.py`) |
| `apps/services_app/` | Services, offres, formations, offres d'emploi |
| `apps/business_partners/` | Programme de partenaires d'affaires (logique métier dans `services.py`) |
| `apps/dashboard/views/` | Tableau de bord d'administration, un module par domaine |
| `apps/messaging/`, `apps/notifications/` | Chat client ↔ équipe, notifications et emails |
| `apps/invoices/` | Facturation (en préparation, pas encore activée) |
| `templates/` | Gabarits : `base.html` (site), `admin/admin_base.html` (dashboard), `partials/` (composants) |
| `static/css/` | `oloustream.css` (système de design), `site.css` (site public), `dashboard.css` (administration) |

## Installation locale

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # puis : DJANGO_ENV= (vide) et DJANGO_DEBUG=True
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

En local, les emails s'affichent dans la console.

## Tests

```bash
DJANGO_DEBUG=True python manage.py test apps
```

Les tests tournent automatiquement sur GitHub avant chaque déploiement : si un test échoue,
le déploiement FTP est bloqué.

## Déploiement (O2Switch)

Chaque push sur `main` lance les tests puis déploie par FTP. Sur le serveur :

1. Créer le fichier `/oloustream/.env` à partir de `.env.example` (clé secrète, base MySQL, email).
   Il n'est jamais envoyé par le déploiement.
2. Après un déploiement qui contient des migrations ou des fichiers statiques :
   ```bash
   source /home/olba9744/virtualenv/oloustream/3.11/bin/activate && cd /home/olba9744/oloustream
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```
3. Redémarrer l'application (cPanel › Setup Python App › Restart).

## Sécurité : à retenir

- Aucun secret dans le code : tout passe par `.env`.
- Les documents sensibles (pièces d'identité, CV, contrats, reçus) se téléchargent via
  `core:protected_file`, qui vérifie les droits. Bloquer l'accès direct au dossier `media/`
  correspondant (copier `deploy/media-prive.htaccess` comme indiqué dans le fichier).
- Toute action qui modifie des données passe par un formulaire POST protégé par CSRF.
- La gestion de l'équipe est réservée aux super-utilisateurs et aux rôles Super Administrateur / Manager.
