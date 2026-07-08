from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import secretaire_required
from apps.emploi_du_temps.models import EmploiDuTemps, Matiere, Niveau, JOUR_CHOICES
from apps.enseignants.models import Enseignant
from apps.core.models import SessionVacances
from datetime import time


HEURES_SLOTS = [
    (time(8, 0), time(9, 0)),
    (time(9, 0), time(10, 0)),
    (time(10, 0), time(11, 0)),
    (time(11, 0), time(12, 0)),
    (time(12, 0), time(13, 0)),
]

JOURS_ORDRE = ['LUNDI', 'MARDI', 'MERCREDI', 'JEUDI', 'VENDREDI']


@login_required
@secretaire_required
def grille(request):
    session_active = SessionVacances.objects.filter(est_active=True).first()

    creneaux = []
    if session_active:
        creneaux = list(EmploiDuTemps.objects.select_related(
            'matiere', 'niveau', 'enseignant__user'
        ).filter(session=session_active))

    # Build grid: list of rows, each row = {debut, fin, creneaux: [None or creneau per day]}
    grille = []
    for debut, fin in HEURES_SLOTS:
        ligne = {'debut': debut, 'fin': fin, 'creneaux': []}
        for jour_code, _ in JOUR_CHOICES:
            match = None
            for c in creneaux:
                if c.jour == jour_code and c.heure_debut == debut and c.heure_fin == fin:
                    match = c
                    break
            ligne['creneaux'].append(match)
        grille.append(ligne)

    context = {
        'jours': JOUR_CHOICES,
        'grille': grille,
        'session_active': session_active,
    }
    return render(request, 'comite/emploi_du_temps/grille.html', context)


@login_required
@secretaire_required
def creneau_ajout(request):
    session_active = SessionVacances.objects.filter(est_active=True).first()
    matieres = Matiere.objects.all()
    niveaux = Niveau.objects.all()
    enseignants = Enseignant.objects.select_related('user').filter(est_actif=True)

    if request.method == 'POST':
        try:
            jour = request.POST.get('jour', '').strip()
            heure_debut = request.POST.get('heure_debut', '').strip()
            heure_fin = request.POST.get('heure_fin', '').strip()
            matiere_id = request.POST.get('matiere', '').strip()
            niveau_id = request.POST.get('niveau', '').strip()
            enseignant_id = request.POST.get('enseignant', '').strip()
            salle = request.POST.get('salle', '').strip()

            if not all([jour, heure_debut, heure_fin, matiere_id, niveau_id, enseignant_id]):
                messages.error(request, 'Tous les champs obligatoires doivent être remplis.')
                return render(request, 'comite/emploi_du_temps/creneau_form.html', {
                    'matieres': matieres,
                    'niveaux': niveaux,
                    'enseignants': enseignants,
                    'jours': JOUR_CHOICES,
                })

            matiere = get_object_or_404(Matiere, pk=matiere_id)
            niveau = get_object_or_404(Niveau, pk=niveau_id)
            enseignant = get_object_or_404(Enseignant, pk=enseignant_id)

            heure_debut = time.fromisoformat(heure_debut)
            heure_fin = time.fromisoformat(heure_fin)

            creneau = EmploiDuTemps(
                session=session_active,
                jour=jour,
                heure_debut=heure_debut,
                heure_fin=heure_fin,
                matiere=matiere,
                niveau=niveau,
                enseignant=enseignant,
                salle=salle,
            )
            creneau.full_clean()
            creneau.save()

            messages.success(request, 'Créneau ajouté avec succès.')
            return redirect('emploi_du_temps_comite:grille_comite')

        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ajout : {e}')

    context = {
        'matieres': matieres,
        'niveaux': niveaux,
        'enseignants': enseignants,
        'jours': JOUR_CHOICES,
    }
    return render(request, 'comite/emploi_du_temps/creneau_form.html', context)


@login_required
@secretaire_required
def creneau_modifier(request, id):
    creneau = get_object_or_404(EmploiDuTemps.objects.select_related('matiere', 'niveau', 'enseignant'), pk=id)
    matieres = Matiere.objects.all()
    niveaux = Niveau.objects.all()
    enseignants = Enseignant.objects.select_related('user').filter(est_actif=True)

    if request.method == 'POST':
        try:
            creneau.jour = request.POST.get('jour', creneau.jour).strip()
            heure_debut = request.POST.get('heure_debut', '').strip()
            heure_fin = request.POST.get('heure_fin', '').strip()
            matiere_id = request.POST.get('matiere', '').strip()
            niveau_id = request.POST.get('niveau', '').strip()
            enseignant_id = request.POST.get('enseignant', '').strip()
            creneau.salle = request.POST.get('salle', '').strip()

            if heure_debut:
                creneau.heure_debut = time.fromisoformat(heure_debut)
            if heure_fin:
                creneau.heure_fin = time.fromisoformat(heure_fin)
            if matiere_id:
                creneau.matiere = get_object_or_404(Matiere, pk=matiere_id)
            if niveau_id:
                creneau.niveau = get_object_or_404(Niveau, pk=niveau_id)
            if enseignant_id:
                creneau.enseignant = get_object_or_404(Enseignant, pk=enseignant_id)

            creneau.full_clean()
            creneau.save()

            messages.success(request, 'Créneau modifié avec succès.')
            return redirect('emploi_du_temps_comite:grille_comite')

        except Exception as e:
            messages.error(request, f'Erreur lors de la modification : {e}')

    context = {
        'creneau': creneau,
        'matieres': matieres,
        'niveaux': niveaux,
        'enseignants': enseignants,
        'jours': JOUR_CHOICES,
        'is_edit': True,
    }
    return render(request, 'comite/emploi_du_temps/creneau_form.html', context)
