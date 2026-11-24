from django.db import migrations

VIDEOS = [
    ("mDGgGi5hjFI", "Tes Blessures d’Enfance Dirigent Encore Ta Vie… Smarty & Bintou Racontent Tout",
     "live", "Émission · Témoignage",
     "Smarty et Bintou se confient sans filtre sur les blessures d’enfance qui façonnent encore nos vies d’adultes.",
     "Émission, Talk"),
    ("uAJghXeFpyU", "Pourquoi tant de femmes BRILLANTES s’éteignent sans le savoir",
     "digital", "Émission · Société",
     "Un échange sincère sur ce qui pousse tant de femmes talentueuses à s’effacer, souvent sans en avoir conscience.",
     "Digital, Société"),
    ("9OXVHp_wnj8", "Comment une Femme a brisé tous les codes du Secteur Minier Africain | Aïda Tamboura",
     "production", "Portrait · Entrepreneuriat",
     "Le parcours d’Aïda Tamboura, qui s’est imposée dans un secteur minier africain longtemps réservé aux hommes.",
     "Portrait, Production"),
    ("F6hcwbLx6pY", "Elle gagne sa VIE avec la MORT : l’incroyable histoire de Céline Bamouni",
     "production", "Portrait · Histoire vraie",
     "L’histoire inattendue de Céline Bamouni, qui a bâti son activité autour des métiers du funéraire.",
     "Portrait, Production"),
]


def seed(apps, schema_editor):
    Video = apps.get_model("core", "VideoRealisation")
    if Video.objects.exists():
        return
    for i, (vid, title, cat, sub, desc, tags) in enumerate(VIDEOS, start=1):
        Video.objects.create(
            youtube_url=f"https://youtu.be/{vid}", youtube_id=vid, title=title, category=cat,
            subtitle=sub, description=desc, tags=tags, order=i * 10,
        )


class Migration(migrations.Migration):
    dependencies = [("core", "0002_video_realisation")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
