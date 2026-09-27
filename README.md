# Oloustream

Site vitrine et plateforme de gestion d'**Oloustream** (Ouagadougou, Burkina Faso) :
studios, live streaming, production audiovisuelle, location de matériel, formations,
recrutement et programme de partenaires d'affaires.

- **Site public** : présentation, studios, matériel, formations, offres, carrières, contact / devis
- **Espace client** : profil, réservations, messagerie avec l'équipe, notifications
- **Espace partenaire** : contrats apportés, commissions, paiements
- **Dashboard d'administration** : réservations, demandes de devis, catalogue, équipe, partenaires, statistiques

---

## Sommaire

1. [Technologies](#1-technologies)
2. [Organisation du code](#2-organisation-du-code)
3. [Lancer le projet en local](#3-lancer-le-projet-en-local)
4. [Utiliser le site en local](#4-utiliser-le-site-en-local)
5. [Variables d'environnement (.env)](#5-variables-denvironnement-env)
6. [Tests](#6-tests)
7. [Déploiement sur O2Switch](#7-déploiement-sur-o2switch)
8. [Rôles et droits d'accès](#8-rôles-et-droits-daccès)
9. [Sécurité](#9-sécurité)
10. [Design : où modifier quoi](#10-design--où-modifier-quoi)
11. [Commandes utiles](#11-commandes-utiles)
12. [Problèmes fréquents](#12-problèmes-fréquents)

---

## 1. Technologies

| Élément | Version / outil |
|---|---|
| Langage | Python 3.11 (3.12 fonctionne aussi) |
| Framework | Django 5.0 |
| Base de données | SQLite en local, MySQL en production |
| Chat temps réel | Django Channels (le chat fonctionne aussi sans, en simple envoi de formulaire) |
| Interface | Bootstrap 5.3, Font Awesome 6, polices Inter et Montserrat |
| API | Django REST Framework + JWT |
| Hébergement | O2Switch (déploiement automatique par FTP via GitHub Actions) |

---

## 2. Organisation du code

```
Oloustream/
├── oloustream/              Configuration : settings.py, urls.py, asgi.py, wsgi.py
├── apps/
│   ├── core/                Accueil, contact/devis, pages légales, robots.txt
│   │   ├── utils.py         Redirections sûres, export Excel, envoi d'email sans plantage
│   │   ├── validators.py    Contrôle des fichiers envoyés (type réel, taille)
│   │   ├── permissions.py   Qui peut gérer l'équipe, accès à l'espace partenaire
│   │   ├── ratelimit.py     Limitation des tentatives (connexion, formulaires)
│   │   ├── files.py         Téléchargement protégé des documents sensibles
│   │   └── tests/           Tests automatisés
│   ├── accounts/            Utilisateurs, connexion, inscription, profil, employés
│   ├── studio/              Studios, matériel, réservations (+ contrôle des chevauchements)
│   ├── services_app/        Services, offres, formations, offres d'emploi
│   ├── business_partners/   Programme de partenaires (logique métier dans services.py)
│   ├── dashboard/views/     Dashboard admin : un fichier par domaine
│   ├── messaging/           Chat client ↔ équipe
│   ├── notifications/       Notifications internes et emails (emailing.py)
│   ├── payments/            Paiements (modèle)
│   ├── invoices/            Facturation (en préparation, pas encore activée)
│   └── content/             (réservé)
├── templates/
│   ├── base.html            Gabarit du site public
│   ├── admin/admin_base.html Gabarit du dashboard
│   ├── partials/            Composants réutilisables (champ de formulaire, pagination, messages)
│   ├── front/               Accueil, contact, pages légales, pied de page
│   ├── user/                Pages client (auth, profil, réservations, catalogue…)
│   ├── partners/            Programme et espace partenaire
│   ├── admin/               Pages du dashboard
│   ├── emails/              Emails envoyés aux clients / partenaires
│   └── 403.html, 404.html, 500.html
├── static/
│   ├── css/oloustream.css   Système de design commun (couleurs, boutons, cartes, tableaux…)
│   ├── css/site.css         Mise en page du site public
│   ├── css/dashboard.css    Mise en page du dashboard
│   ├── js/site.js           Menus, confirmations, aperçu d'image…
│   └── img/                 Logo, images, logos partenaires
├── deploy/                  Fichiers à copier sur le serveur (.htaccess de protection)
├── .env.example             Modèle du fichier de configuration secrète
├── requirements.txt         Dépendances Python
└── manage.py
```

---

## 3. Lancer le projet en local

### Étape 1 — Prérequis

- **Python 3.11 ou plus récent** : `python3 --version`
- **Git**
- Sous **Linux (Ubuntu/Debian)** : `sudo apt install -y python3-venv`
- Sous **Windows** : installer Python depuis python.org en cochant « Add Python to PATH ».

> Les dépendances sont séparées en deux fichiers :
> - `requirements.txt` : tout ce qu'il faut pour travailler **en local** (base SQLite, aucune installation MySQL nécessaire) ;
> - `requirements-prod.txt` : la même chose **+ le pilote MySQL** (`mysqlclient`), utilisé seulement sur le serveur.

### Étape 2 — Récupérer le code

```bash
git clone git@github.com:Koumbia-pro/Oloustream.git
cd Oloustream
```

(Si le dossier existe déjà : `cd Oloustream` puis `git pull`.)

### Étape 3 — Créer l'environnement virtuel

**Linux / macOS :**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell) :**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

Le début de la ligne de commande affiche alors `(venv)`. Il faut réactiver l'environnement
(`source venv/bin/activate`) à chaque nouveau terminal.

> Utiliser **un seul** environnement virtuel. Si VS Code en a créé un second (`.venv`),
> choisir le même dans VS Code (`Ctrl+Maj+P` › « Python: Select Interpreter » › `./venv/bin/python`)
> ou supprimer l'un des deux.

### Étape 4 — Installer les dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Étape 5 — Créer le fichier `.env` local

Copier le modèle :

```bash
cp .env.example .env          # Windows : copy .env.example .env
```

Puis **ouvrir `.env` et le modifier pour le local** :

```ini
DJANGO_ENV=
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=
```

- `DJANGO_ENV` doit être **vide** en local (sinon Django cherche la base MySQL de production).
- `DJANGO_DEBUG=True` affiche les erreurs détaillées et sert les images/CSS.
- `DJANGO_SECRET_KEY` peut rester vide en local.
- Les autres lignes (MySQL, email) peuvent rester vides : en local, les emails s'affichent
  dans le terminal au lieu d'être envoyés.

### Étape 6 — Créer la base de données

```bash
python manage.py migrate
```

Cela crée le fichier `db.sqlite3` avec toutes les tables.

### Étape 7 — Charger les régions du Burkina Faso (programme partenaires)

```bash
python manage.py load_regions
```

### Étape 8 — Créer un compte administrateur

```bash
python manage.py createsuperuser
```

Répondre aux questions (nom d'utilisateur, email, mot de passe).

### Étape 9 — Démarrer le serveur

```bash
python manage.py runserver
```

Ouvrir **http://127.0.0.1:8000** dans le navigateur. Pour arrêter le serveur : `Ctrl + C`.

### Récapitulatif (après la première installation)

```bash
cd Oloustream
source venv/bin/activate        # Windows : venv\Scripts\Activate.ps1
python manage.py migrate        # seulement s'il y a eu des changements
python manage.py runserver
```

---

## 4. Utiliser le site en local

| Adresse | Contenu |
|---|---|
| http://127.0.0.1:8000/ | Site public |
| http://127.0.0.1:8000/accounts/login/ | Connexion (identifiant **ou** email) |
| http://127.0.0.1:8000/dashboard/ | Dashboard d'administration (compte staff) |
| http://127.0.0.1:8000/admin/ | Administration avancée Django (super-utilisateur) |
| http://127.0.0.1:8000/partenaires/programme/ | Programme partenaires |
| http://127.0.0.1:8000/contact/ | Formulaire de contact / devis |

**Pour avoir des données à afficher**, se connecter au dashboard avec le super-utilisateur
puis créer au moins : un studio, un service, un équipement et une formation.

**Tester l'espace partenaire** : déposer une candidature sur `/partenaires/postuler/`,
puis l'approuver dans *Dashboard › Partenaires d'affaires › Candidatures*. L'email
d'activation (avec le lien pour créer le mot de passe) s'affiche dans le terminal.

---

## 5. Variables d'environnement (.env)

Le fichier `.env` contient tous les secrets. **Il ne doit jamais être envoyé sur GitHub**
(il est déjà ignoré par `.gitignore`).

| Variable | Local | Production (O2Switch) |
|---|---|---|
| `DJANGO_ENV` | *(vide)* | `production` |
| `DJANGO_DEBUG` | `True` | ignoré (toujours désactivé en production) |
| `DJANGO_SECRET_KEY` | *(vide possible)* | **obligatoire**, longue et aléatoire |
| `DJANGO_ALLOWED_HOSTS` | *(défaut ok)* | `oloustream.com,www.oloustream.com` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | *(défaut ok)* | `https://oloustream.com,https://www.oloustream.com` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | inutiles | accès MySQL |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS` | inutiles | serveur SMTP |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | inutiles | identifiants SMTP (mot de passe d'application Gmail) |
| `DEFAULT_FROM_EMAIL` | — | `Oloustream <info@oloustream.com>` |
| `ADMIN_EMAIL` | — | adresse qui reçoit les demandes de devis et candidatures |
| `SITE_URL` | — | `https://oloustream.com` (utilisé dans les liens des emails) |

**Générer une clé secrète :**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 6. Tests

```bash
DJANGO_DEBUG=True python manage.py test apps
```

(Windows PowerShell : `$env:DJANGO_DEBUG="True"; python manage.py test apps`)

Les tests vérifient notamment : le blocage après 5 connexions ratées, l'accès au chat,
les droits sur l'équipe, les documents protégés, la validation des fichiers, les
contrats et commissions des partenaires, les conflits de réservation et le formulaire de contact.

Vérifications complémentaires :
```bash
python manage.py check                          # configuration
python manage.py makemigrations --check         # aucune migration oubliée
```

---

## 7. Déploiement sur O2Switch

### Fonctionnement

Chaque `git push` sur la branche **`main`** déclenche GitHub Actions
(`.github/workflows/main.yml`) :

1. **Tests** : vérifications Django + tests automatisés.
2. **Déploiement FTP** vers `/oloustream/` sur le serveur, **uniquement si les tests passent**.

Les fichiers `.env`, `media/`, `db.sqlite3`, `logs/` et `staticfiles/` ne sont jamais envoyés.

> Travailler sur une autre branche (ex. `git checkout -b ma-modif`) permet de modifier
> sans rien mettre en ligne. On fusionne dans `main` seulement quand c'est prêt.

### Première mise en production de cette version

⚠️ **À faire dans cet ordre, sinon le site ne démarre pas.**

1. **Créer le fichier `.env` sur le serveur** (via le gestionnaire de fichiers cPanel ou en SSH),
   dans `/home/olba9744/oloustream/.env`, à partir de `.env.example`, avec
   `DJANGO_ENV=production`, une nouvelle `DJANGO_SECRET_KEY`, les accès MySQL et email.
2. **Fusionner la branche dans `main`** puis pousser :
   ```bash
   git checkout main
   git merge refonte-complete
   git push origin main
   ```
3. **Sur le serveur (SSH ou Terminal cPanel)** :
   ```bash
   source /home/olba9744/virtualenv/oloustream/3.11/bin/activate
   cd /home/olba9744/oloustream
   pip install -r requirements-prod.txt
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py check --deploy
   ```
4. **Redémarrer l'application** : cPanel › *Setup Python App* › *Restart*.
5. **Protéger les documents sensibles** : copier `deploy/media-prive.htaccess` sous le nom
   `.htaccess` dans les dossiers listés au début de ce fichier.

### Mises à jour suivantes

Pousser sur `main`, puis sur le serveur si nécessaire :
```bash
source /home/olba9744/virtualenv/oloustream/3.11/bin/activate && cd /home/olba9744/oloustream
python manage.py migrate                    # s'il y a de nouvelles migrations
python manage.py collectstatic --noinput    # si le CSS/JS/images ont changé
```
puis redémarrer l'application.

### Journaux d'erreurs

Les erreurs sont enregistrées dans `logs/oloustream.log` sur le serveur.

---

## 8. Rôles et droits d'accès

| Profil | Accès |
|---|---|
| Visiteur | Site public, contact/devis, candidature partenaire |
| Client (compte créé via inscription) | + réservations, messagerie, notifications, profil |
| Partenaire d'affaires (candidature approuvée, compte actif) | + espace partenaire (contrats, commissions) |
| Membre de l'équipe (`is_staff`) | + dashboard (réservations, catalogue, partenaires, messagerie) |
| Super Administrateur / Manager / super-utilisateur | + gestion de l'équipe (employés, rôles, mots de passe) |
| Super-utilisateur Django | + administration avancée `/admin/` |

Règles de protection :
- Un Manager ne peut ni modifier un Super Administrateur ou un super-utilisateur, ni attribuer le rôle Super Administrateur.
- Personne ne peut supprimer son propre compte depuis le dashboard.
- Un partenaire suspendu n'a plus accès à son espace.

---

## 9. Sécurité

- **Secrets** : uniquement dans `.env`, jamais dans le code.
- **Production** : HTTPS obligatoire, cookies sécurisés, HSTS, protection contre l'affichage dans une iframe.
- **Connexion** : blocage 15 minutes après 5 échecs ; connexion possible avec l'email.
- **Formulaires publics** : champ piège anti-robots et limite de 5 envois par heure sur le contact.
- **Fichiers envoyés** : type réel vérifié (PDF / images), 5 à 10 Mo maximum.
- **Documents sensibles** (pièces d'identité, CV, contrats, reçus) : téléchargement uniquement via
  `/fichiers/…`, qui vérifie les droits de la personne connectée.
- **Actions sensibles** (valider, rejeter, annuler, supprimer, se déconnecter) : formulaires POST protégés CSRF.
- **Chat** : seul le client concerné et l'équipe peuvent rejoindre une conversation.
- **Exports Excel** : protégés contre l'injection de formules.
- **Partenaires** : aucun mot de passe envoyé par email ; le partenaire reçoit un lien sécurisé pour créer le sien.

---

## 10. Design : où modifier quoi

| Je veux changer… | Fichier |
|---|---|
| Les couleurs, polices, boutons, cartes, badges | `static/css/oloustream.css` (variables `--ol-…` en haut du fichier) |
| Le menu, l'accueil, le pied de page du site | `templates/base.html`, `templates/front/home.html`, `templates/front/footer.html`, `static/css/site.css` |
| Le téléphone, l'email, l'adresse, les réseaux sociaux | `apps/core/context_processors.py` (dictionnaire `SITE`) |
| Les chiffres clés de l'accueil (projets, vues, pays) | `apps/core/views.py` (`KEY_FIGURES`) |
| Le menu du dashboard | `templates/admin/admin_base.html` |
| L'apparence des emails | `templates/emails/_base_email.html` |

Pour créer une nouvelle page du dashboard, copier la structure de `templates/admin/services/`
(liste, fiche, formulaire, suppression).

---

## 11. Commandes utiles

```bash
python manage.py runserver                  # démarrer le serveur local
python manage.py migrate                    # appliquer les changements de base de données
python manage.py makemigrations             # après modification d'un modèle
python manage.py createsuperuser            # créer un administrateur
python manage.py changepassword <nom>       # changer un mot de passe
python manage.py load_regions               # charger les régions du Burkina Faso
python manage.py collectstatic --noinput    # regrouper CSS/JS/images (production)
python manage.py shell                      # console Python avec le projet chargé
DJANGO_DEBUG=True python manage.py test apps  # lancer les tests
```

---

## 12. Problèmes fréquents

**`pip install` échoue sur `mysqlclient` (« Can not find valid pkg-config name »)**
→ En local, installer `requirements.txt` (sans MySQL), pas `requirements-prod.txt`.
Si vous avez vraiment besoin de MySQL en local (Ubuntu) :
`sudo apt install -y default-libmysqlclient-dev build-essential pkg-config python3-dev`.

**`No module named 'django'`**
→ L'environnement virtuel n'est pas activé (`source venv/bin/activate`), ou l'installation des
dépendances s'est arrêtée sur une erreur : relancer `pip install -r requirements.txt` et vérifier
qu'elle se termine par « Successfully installed ».

**`ImproperlyConfigured: DJANGO_SECRET_KEY doit être défini en production`**
→ `DJANGO_ENV=production` est dans votre `.env` local. Le vider en local, ou ajouter la clé sur le serveur.

**Le CSS ne s'affiche pas en local**
→ Vérifier `DJANGO_DEBUG=True` dans `.env`.

**Le CSS ne s'affiche pas en production**
→ Lancer `python manage.py collectstatic --noinput` puis redémarrer l'application.

**`no such table` / `Table doesn't exist`**
→ Lancer `python manage.py migrate`.

**« Trop de tentatives de connexion »**
→ Attendre 15 minutes, ou utiliser « Mot de passe oublié ». En local, supprimer le dossier `.cache/`.

**Les emails ne partent pas en production**
→ Vérifier `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` dans `.env` (pour Gmail : mot de passe
d'application, pas le mot de passe du compte), puis consulter `logs/oloustream.log`.
Un email en échec ne bloque jamais l'utilisateur : l'action est enregistrée quand même.

**Page 404 sur un document (pièce d'identité, CV…)**
→ Le fichier n'existe pas sur le serveur, ou la personne connectée n'a pas le droit de le voir.
