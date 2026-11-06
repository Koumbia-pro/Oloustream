# Rapport d’import du catalogue Oloustream

Import réalisé depuis [catalogue_oloustream_complet.xlsx](./catalogue_oloustream_complet.xlsx).

## Données importées

- Services : 5 lignes traitées
- Studios : 2 lignes traitées (3 studios présents au total avec les données existantes)
- Équipements : 5 lignes traitées
- Formations : 3 lignes traitées
- Offres : 3 lignes traitées
- Partenaires : 2 lignes traitées, désactivés (`active=False`) car signalés comme données de démonstration

Les images disponibles dans `static/img/generated/` ont été associées aux services, studios, équipements et formations correspondants.

## Fichiers encore absents

- `service-drone-card.png`
- `service-photo-card.png`
- `brochure-montage-video.pdf`
- `brochure-live.pdf`
- `brochure-cadrage.pdf`
- `logo-partenaire-fournisseur.png`
- `logo-partenaire-media.png`

L’image `service-drone-card.png` est également référencée par une ligne d’équipement dans le catalogue.

## Contrôle

La commande `manage.py check` passe sans erreur. Les données pourront être complétées ou corrigées lorsque les noms définitifs, les fichiers manquants et les informations réelles des partenaires seront disponibles.
