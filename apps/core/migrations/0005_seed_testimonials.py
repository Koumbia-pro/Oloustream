from django.db import migrations

# Témoignages déjà affichés sur l'accueil avant qu'ils deviennent gérables depuis le tableau de bord.
TESTIMONIALS = [
    ("Grâce à Oloustream, nous avons professionnalisé nos conférences en ligne avec une qualité d'image "
     "et de son digne des grandes chaînes.", "Responsable communication", "Entreprise événementielle, Ouagadougou"),
    ("L'équipe technique est à l'écoute, réactive et force de proposition pour mettre en valeur nos "
     "événements en direct.", "Chargé de projet digital", "Institution publique"),
    ("Un vrai partenaire, pas seulement un prestataire. De la préparation au rendu final, tout est maîtrisé.",
     "Créateur de contenu", "Chaîne YouTube"),
]


def seed(apps, schema_editor):
    Testimonial = apps.get_model("core", "Testimonial")
    if Testimonial.objects.exists():
        return
    for i, (quote, role, organization) in enumerate(TESTIMONIALS, start=1):
        Testimonial.objects.create(quote=quote, author_role=role, organization=organization, order=i * 10)


class Migration(migrations.Migration):
    dependencies = [("core", "0004_testimonial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
