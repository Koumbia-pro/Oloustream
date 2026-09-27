"""
Vues du dashboard d'administration, regroupées par domaine :

- home.py              tableau de bord principal
- employees.py         équipe (réservé aux administrateurs)
- equipments.py        matériel
- reservations.py      réservations
- catalog.py           services, offres, formations
- partners.py          partenaires (logos / institutions)
- studios.py           studios
- business_partners.py programme de partenaires d'affaires
- contacts.py          demandes de contact / devis
"""
from .business_partners import *  # noqa: F401,F403
from .catalog import *  # noqa: F401,F403
from .contacts import *  # noqa: F401,F403
from .employees import *  # noqa: F401,F403
from .equipments import *  # noqa: F401,F403
from .home import *  # noqa: F401,F403
from .partners import *  # noqa: F401,F403
from .reservations import *  # noqa: F401,F403
from .studios import *  # noqa: F401,F403
