from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from decimal import Decimal

from apps.accounts.decorators import enseignant_required
from apps.core.models import SessionVacances
from apps.emploi_du_temps.models import Niveau, EmploiDuTemps, Matiere
from apps.inscriptions.models import Inscription
from apps.notes.models import Note, CoefficientMatiere, BulletinConfig


def _matiere_url(niveau_id, matiere_id=None):
    """Builds the URL for the notes page, optionally with a matiere parameter."""
    url = reverse('notes_enseignant:saisie_notes', args=[niveau_id])
    if matiere_id:
        url += f'?matiere={matiere_id}'
    return url


@login_required
@enseignant_required
def liste_classes(request):
    """Affiche les classes où l'enseignant intervient."""
    enseignant = request.user.enseignant
    session = SessionVacances.objects.filter(est_active=True).first()

    if not session:
        messages.warning(request, 'Aucune session active pour le moment.')
        return render(request, 'enseignant/notes/liste_classes.html', {'classes': []})

    niveaux_ids = EmploiDuTemps.objects.filter(
        enseignant=enseignant, session=session
    ).values_list('niveau_id', flat=True).distinct()

    niveaux = Niveau.objects.filter(id__in=niveaux_ids)

    configs = {
        c.niveau_id: c
        for c in BulletinConfig.objects.filter(
            niveau_id__in=niveaux_ids, session=session
        )
    }

    classes_info = []
    for niveau in niveaux:
        config = configs.get(niveau.id)
        saisie_ouverte = config.saisie_ouverte if config else False

        eleves = Inscription.objects.filter(niveau=niveau, session=session).count()
        notes_saisies = Note.objects.filter(
            enseignant=enseignant, session=session,
            inscription__niveau=niveau
        ).values('inscription').distinct().count()

        classes_info.append({
            'niveau': niveau,
            'effectif': eleves,
            'notes_saisies': notes_saisies,
            'saisie_ouverte': saisie_ouverte,
        })

    context = {'classes': classes_info, 'session': session, 'enseignant': enseignant}
    return render(request, 'enseignant/notes/liste_classes.html', context)


@login_required
@enseignant_required
def saisie_notes(request, niveau_id):
    """Saisie des notes pour les élèves d'une classe."""
    enseignant = request.user.enseignant
    session = SessionVacances.objects.filter(est_active=True).first()
    niveau = get_object_or_404(Niveau, pk=niveau_id)

    if not session:
        messages.error(request, 'Aucune session active.')
        return redirect('notes_enseignant:liste_classes')

    config = BulletinConfig.objects.filter(niveau=niveau, session=session).first()
    if config and not config.saisie_ouverte:
        messages.error(request, 'La saisie des notes est fermée pour cette classe.')
        return redirect('notes_enseignant:liste_classes')

    if not EmploiDuTemps.objects.filter(
        enseignant=enseignant, session=session, niveau=niveau
    ).exists():
        messages.error(request, "Vous n'intervenez pas dans cette classe.")
        return redirect('notes_enseignant:liste_classes')

    # Matières de l'enseignant pour ce niveau
    matieres_ids = list(dict.fromkeys(
        EmploiDuTemps.objects.filter(
            enseignant=enseignant, session=session, niveau=niveau
        ).values_list('matiere_id', flat=True).distinct()
    ))
    matieres_objs = Matiere.objects.filter(id__in=matieres_ids)

    coeffs = {
        c.matiere_id: c.coefficient
        for c in CoefficientMatiere.objects.filter(
            matiere_id__in=matieres_ids, niveau=niveau
        )
    }

    eleves = Inscription.objects.filter(
        niveau=niveau, session=session
    ).order_by('nom_eleve', 'prenom_eleve')

    if request.method == 'POST':
        matiere_id = request.POST.get('matiere_id')
        if not matiere_id or int(matiere_id) not in matieres_ids:
            messages.error(request, 'Matière invalide.')
            return redirect(_matiere_url(niveau_id))

        matiere_id = int(matiere_id)
        matiere = get_object_or_404(Matiere, pk=matiere_id)
        notes_enregistrees = 0

        for eleve in eleves:
            note_val = request.POST.get(f'note_{eleve.id}', '').strip()
            if note_val:
                try:
                    note_dec = Decimal(note_val)
                    if note_dec < 0 or note_dec > 20:
                        messages.warning(request, f"Note de {eleve.nom_eleve} {eleve.prenom_eleve} ignorée (doit être 0-20).")
                        continue
                    Note.objects.update_or_create(
                        inscription=eleve, matiere=matiere, session=session,
                        enseignant=enseignant,
                        defaults={
                            'note': note_dec,
                            'observation': request.POST.get(f'obs_{eleve.id}', '').strip(),
                        }
                    )
                    notes_enregistrees += 1
                except (ValueError, Decimal.InvalidOperation):
                    messages.warning(request, f"Note invalide pour {eleve.nom_eleve} {eleve.prenom_eleve}.")

        messages.success(request, f'{notes_enregistrees} note(s) enregistrée(s) pour {matiere.nom}.')
        return redirect(_matiere_url(niveau_id, matiere_id))

    # GET — matière active
    matiere_active = None
    matiere_active_id = request.GET.get('matiere')
    if matiere_active_id and int(matiere_active_id) in matieres_ids:
        matiere_active = get_object_or_404(Matiere, pk=int(matiere_active_id))

    # Notes existantes par élève et matière
    notes_toutes = Note.objects.filter(
        inscription__in=eleves, matiere_id__in=matieres_ids,
        session=session, enseignant=enseignant
    ).select_related('matiere')

    notes_par_eleve = {}
    count_matiere_active = 0
    for note in notes_toutes:
        notes_par_eleve.setdefault(note.inscription_id, {})[note.matiere_id] = note
        if matiere_active and note.matiere_id == matiere_active.id:
            count_matiere_active += 1

    eleves_data = []
    for eleve in eleves:
        note_obj = None
        if matiere_active and eleve.id in notes_par_eleve:
            note_obj = notes_par_eleve[eleve.id].get(matiere_active.id)
        eleves_data.append({'eleve': eleve, 'note': note_obj})

    context = {
        'enseignant': enseignant, 'niveau': niveau, 'session': session,
        'matieres': matieres_objs, 'matiere_active': matiere_active,
        'coefficients': coeffs, 'eleves_data': eleves_data,
        'count_notes_matiere_active': count_matiere_active,
    }
    return render(request, 'enseignant/notes/saisie_notes.html', context)
