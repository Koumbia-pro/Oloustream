# Déploiement Oloustream sur O2Switch/cPanel

Ce guide cible le sous-domaine `oloustream.groupeoloustream.com` et une
application Python WSGI gérée par Passenger.

## 1. Sous-domaine et certificat

Dans cPanel, ouvrir **Domaines → Sous-domaines** et créer :

- Sous-domaine : `oloustream`
- Domaine : `groupeoloustream.com`
- Racine des documents : le dossier de l'application, par exemple `oloustream`

Vérifier ensuite que le DNS du sous-domaine pointe vers O2Switch. Une fois le
DNS propagé, activer le certificat SSL depuis **SSL/TLS Status** ou AutoSSL.

## 2. Application Python

Dans **Setup Python App** ou **Application Manager**, créer une application
avec les paramètres suivants :

- Python : 3.11 si disponible
- Application root : `oloustream`
- Application URL : `oloustream.groupeoloustream.com`
- Startup file : `passenger_wsgi.py`
- Entry point : `application`

Le fichier `passenger_wsgi.py` doit être à la racine du projet.

## 3. Code et environnement virtuel

Envoyer le dépôt dans la racine de l'application, sans envoyer `.env`,
`db.sqlite3`, `media/`, `logs/` ou `staticfiles/` depuis la machine locale.

Depuis le Terminal cPanel, adapter le chemin affiché par cPanel puis exécuter :

```bash
cd ~/oloustream
source ~/virtualenv/oloustream/3.11/bin/activate
python -m pip install -r requirements-prod.txt
```

Le chemin exact du virtualenv dépend de la configuration choisie dans cPanel.

## 4. Base MySQL

Dans cPanel : **Bases de données → MySQL Databases** :

1. créer une base ;
2. créer un utilisateur ;
3. attribuer l'utilisateur à la base avec tous les privilèges ;
4. noter les noms complets préfixés par le compte cPanel.

## 5. Fichier `.env`

Créer `~/oloustream/.env` sur le serveur. Ne jamais le commiter :

```ini
DJANGO_ENV=production
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=REMPLACER_PAR_UNE_CLE_LONGUE_ET_ALEATOIRE
DJANGO_ALLOWED_HOSTS=oloustream.groupeoloustream.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://oloustream.groupeoloustream.com

DB_NAME=PREFIXE_NOM_BASE
DB_USER=PREFIXE_UTILISATEUR
DB_PASSWORD=MOT_DE_PASSE_MYSQL
DB_HOST=localhost
DB_PORT=3306

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=adresse-email
EMAIL_HOST_PASSWORD=mot-de-passe-application
DEFAULT_FROM_EMAIL=Oloustream <adresse-email>
ADMIN_EMAIL=adresse-email
SITE_URL=https://oloustream.groupeoloustream.com
```

Si le site doit aussi répondre sur le domaine principal, ajouter ses noms dans
`DJANGO_ALLOWED_HOSTS` et `DJANGO_CSRF_TRUSTED_ORIGINS`.

## 6. Initialisation Django

Toujours avec le virtualenv activé :

```bash
cd ~/oloustream
python manage.py check
python manage.py check --deploy
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py load_regions
python manage.py createsuperuser
mkdir -p tmp logs media staticfiles
touch tmp/restart.txt
```

## 7. Documents privés

Créer les dossiers privés utilisés par le projet et y copier le fichier
`deploy/media-prive.htaccess` sous le nom `.htaccess` :

```text
media/partners/documents/
media/partners/contracts/
media/partners/payments/
media/contracts/
media/job_applications/cv/
```

Les fichiers médias déjà existants doivent être transférés séparément dans
`media/` si nécessaire.

## 8. Redémarrage et vérification

Après chaque mise à jour :

```bash
cd ~/oloustream
source ~/virtualenv/oloustream/3.11/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
touch tmp/restart.txt
```

Tester ensuite :

- `https://oloustream.groupeoloustream.com/`
- `/accounts/login/`
- `/admin/`
- `/dashboard/`
- `/robots.txt`

En cas d'erreur 500, consulter les logs de l'application Python dans cPanel
et `logs/oloustream.log`.
