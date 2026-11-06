# Organisation des données Oloustream

Le fichier [catalogue_oloustream_template.xlsx](./catalogue_oloustream_template.xlsx) est organisé par onglets. Remplir une ligne par élément.

## Onglets à remplir

- **Services** : live streaming, production vidéo, post-production, conseil, location et autres prestations.
- **Studios** : nom, description, dimensions, équipements, prix et disponibilité.
- **Equipements** : caméras, micros, lumières, accessoires et matériel de régie.
- **Formations** : titre, programme, niveau, mode, prix, calendrier, certification et brochure.
- **Offres** : promotions liées à un service, pour une période précise.
- **Partenaires** : nom, logo, site web et type de partenariat.
- **Images** : inventaire de toutes les images avec leur usage et leur texte alternatif.
- **Listes_valeurs** : valeurs acceptées par l'application pour éviter les erreurs de saisie.

## Organisation des fichiers images

Créer un dossier `images/` à côté du fichier Excel et utiliser exactement les noms indiqués dans les colonnes `image_file`, `photo_file`, `logo_file` ou `brochure_file`.

Exemple :

```text
catalogue_oloustream_template.xlsx
images/
├── studio-podcast.webp
├── camera-cinema.webp
├── formation-montage.webp
├── logo-partenaire.png
└── brochure-live.pdf
```

Dans Excel, écrire seulement le nom du fichier, par exemple : `studio-podcast.webp`.

## Règles importantes

- Utiliser les dates au format `YYYY-MM-DD`, par exemple `2026-11-15`.
- Utiliser uniquement `TRUE` ou `FALSE` pour les colonnes oui/non.
- Les prix doivent être indiqués en FCFA, sans écrire `FCFA` dans la cellule : `250000`.
- Pour une catégorie ou un service existant, utiliser son nom exact ou son slug.
- Ne pas fusionner les cellules.
- Ne pas supprimer les noms de colonnes de la première ligne.
- Une ligne correspond à un seul service, studio, équipement, formation, offre ou partenaire.
- Pour les champs longs, écrire une phrase claire ou séparer les éléments par des virgules.

## Exemple de formation

```text
Titre : Montage vidéo professionnel
Niveau : BEGINNER
Mode : ONSITE
Lieu : Ouagadougou
Durée : 24
Prix : 150000
Certification : TRUE
Image : formation-montage.webp
```

Après remplissage, fournir le fichier Excel avec le dossier `images/`. Je pourrai ensuite importer et relier les données au site.
