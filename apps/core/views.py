from django.shortcuts import render

from apps.core.models import SessionVacances
from apps.emploi_du_temps.models import Matiere
from apps.enseignants.models import Enseignant
from apps.inscriptions.models import Inscription


def accueil(request):
    session_active = SessionVacances.objects.filter(est_active=True).first()

    context = {
        'session_active': session_active,
        'nb_enseignants': _count_enseignants_actifs(),
        'nb_inscriptions': _count_inscriptions(session_active),
        'nb_matieres': _count_matieres(),
    }
    return render(request, 'public/index.html', context)


def _count_enseignants_actifs():
    try:
        return Enseignant.objects.filter(est_actif=True).count()
    except Exception:
        return 0


def _count_inscriptions(session_active):
    try:
        if session_active:
            return Inscription.objects.filter(session=session_active).count()
        return 0
    except Exception:
        return 0


def _count_matieres():
    try:
        return Matiere.objects.count()
    except Exception:
        return 0
