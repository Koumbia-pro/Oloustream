# Prompt à donner à une IA pour remplir le catalogue Oloustream

Copie-colle le texte ci-dessous dans l'IA avec les fichiers suivants :

- `catalogue_oloustream_template.xlsx`
- le dossier `images/`
- la plaquette PDF Oloustream 2026
- éventuellement les anciennes données du site ou les documents commerciaux

```text
Tu es responsable de la préparation du catalogue commercial d'Oloustream, une entreprise burkinabè spécialisée dans la production audiovisuelle, les studios, le live streaming, la location de matériel, les formations et l'accompagnement événementiel.

Ta mission est de remplir entièrement le fichier Excel `catalogue_oloustream_template.xlsx` à partir des documents, de la plaquette PDF et des images fournis.

OBJECTIF
Créer un catalogue propre, complet, cohérent et directement exploitable pour alimenter le site web Oloustream.

FICHIERS À ANALYSER
1. Le fichier Excel `catalogue_oloustream_template.xlsx`.
2. Le dossier `images/` et toutes ses sous-dossiers.
3. La plaquette officielle Oloustream 2026.
4. Tous les documents commerciaux complémentaires fournis.

RÈGLES ABSOLUES
- Ne jamais inventer un prix, une date, une caractéristique technique, un partenaire ou une statistique.
- Si une information est absente, laisser la cellule vide et noter l'information dans une colonne `notes` si elle existe.
- Ne pas supprimer, renommer ou déplacer les onglets du fichier Excel.
- Ne pas supprimer la première ligne qui contient les noms des colonnes.
- Remplir une ligne par élément.
- Utiliser les valeurs autorisées dans l'onglet `Listes_valeurs`.
- Utiliser les dates au format `YYYY-MM-DD`.
- Utiliser uniquement `TRUE` ou `FALSE` pour les champs oui/non.
- Écrire les prix uniquement en chiffres, sans écrire `FCFA` dans la cellule.
- Conserver les accents et les noms officiels.
- Ne pas mettre de texte dans les cellules réservées aux nombres ou aux dates.
- Ne pas créer de doublons.

GESTION DES IMAGES
- Examiner toutes les images du dossier `images/`.
- Associer chaque image à l'élément correspondant grâce à son contenu, son nom et son contexte.
- Dans Excel, écrire uniquement le nom exact du fichier dans la colonne adaptée : `image_file`, `photo_file`, `logo_file` ou `brochure_file`.
- Ne jamais intégrer une image directement dans une cellule Excel.
- Vérifier que chaque fichier indiqué existe réellement dans le dossier `images/`.
- Si une image ne peut pas être associée avec certitude, la placer dans l'onglet `Images` avec la mention `À vérifier`.
- Remplir un texte alternatif descriptif dans l'onglet `Images` pour chaque image utilisée.

REMPLISSAGE DES ONGLETS

1. SERVICES
Ajouter les prestations proposées par Oloustream, notamment : live streaming, production audiovisuelle, captation vidéo, post-production, location de matériel, formation, conseil et prestations sur mesure.
Pour chaque service, remplir le nom, le slug, les descriptions, la catégorie, le type, le prix si présent dans les documents, la durée, le lieu, le niveau de complexité, les besoins en studio ou en matériel, l'image et le statut.

2. STUDIOS
Ajouter chaque studio disponible.
Remplir le nom, le code, la description, le type de studio, l'adresse, la ville, le pays, l'image, les dimensions, la superficie, l'éclairage, les caméras, microphones, lumières, écrans, régie, accessoires, tarifs horaires, demi-journée, journée, options, capacité, techniciens requis, horaires et disponibilité.
Si la superficie n'est pas donnée mais que la longueur et la largeur sont disponibles, calculer longueur × largeur.

3. EQUIPEMENTS
Ajouter chaque caméra, objectif, microphone, lumière, trépied, accessoire, régie ou autre matériel.
Remplir le nom, la marque, le modèle, la catégorie, le numéro de série si disponible, le prix d'achat si disponible, le statut, la disponibilité à la location, l'emplacement, les spécifications, les accessoires, les dates de maintenance, la photo et le manuel PDF.

4. FORMATIONS
Ajouter chaque formation audiovisuelle.
Remplir le titre, le slug, les descriptions, la catégorie, le niveau, le mode, le lieu, les objectifs, les prérequis, le public cible, le programme détaillé, la durée, le prix, la certification, le nombre de places, les dates, les horaires, l'image et la brochure.

5. OFFRES
Ajouter uniquement les promotions clairement indiquées dans les documents.
Associer chaque offre au nom exact ou au slug du service concerné.
Remplir le titre, la description, le pourcentage de réduction, la date de début, la date de fin et le statut.
Si aucune offre active n'est documentée, laisser l'onglet vide et écrire une note dans un rapport séparé.

6. PARTENAIRES
Ajouter les partenaires officiellement confirmés dans les documents ou déjà présents dans les données du site.
Remplir le nom officiel, le logo, le site web, le contact si disponible, le type de partenariat, l'adresse et le statut actif.
Ne pas considérer automatiquement un logo visible sur une plaquette comme un partenaire confirmé sans preuve claire.

7. IMAGES
Créer une ligne pour chaque image fournie.
Indiquer son nom de fichier, son usage, la page ou section prévue, son texte alternatif, sa source ou son copyright, la présence d'une version WebP et les notes éventuelles.

CONTRÔLES À EFFECTUER AVANT DE RENDRE LE FICHIER
- Vérifier qu'aucune ligne importante n'est dupliquée.
- Vérifier que chaque service, studio, formation, équipement et partenaire possède un nom clair.
- Vérifier que les dates sont valides et cohérentes.
- Vérifier que les dates de fin ne précèdent pas les dates de début.
- Vérifier que les prix sont numériques et positifs.
- Vérifier que les images référencées existent réellement.
- Vérifier que les valeurs comme `service_type`, `level`, `mode`, `status` et `partnership_type` respectent l'onglet `Listes_valeurs`.
- Vérifier les fautes d'orthographe et harmoniser les majuscules.
- Ne pas remplir les informations inconnues par des suppositions.

LIVRABLES ATTENDUS
1. Le fichier Excel rempli : `catalogue_oloustream_rempli.xlsx`.
2. Un rapport `rapport-verification-oloustream.md` contenant :
   - le nombre de lignes ajoutées dans chaque onglet ;
   - les images associées avec succès ;
   - les informations manquantes ;
   - les éléments nécessitant une validation humaine ;
   - les éventuels doublons ou incohérences détectés.
3. Une liste des images non utilisées et la raison.

Avant de terminer, relire toutes les données et signaler clairement ce qui est certain, ce qui provient de la plaquette et ce qui doit être confirmé par l'équipe Oloustream.
```

Après le remplissage, récupérer le fichier Excel final, le rapport et le dossier `images/` pour me les transmettre afin que je puisse importer les contenus dans le site.
