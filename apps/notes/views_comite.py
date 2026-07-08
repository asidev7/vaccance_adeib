from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.db.models import Sum
from decimal import Decimal

from apps.accounts.decorators import staff_comite_required
from apps.core.models import SessionVacances
from apps.emploi_du_temps.models import Niveau
from apps.inscriptions.models import Inscription
from apps.notes.models import (
    Note, CoefficientMatiere, BulletinConfig, BulletinGenere
)
from apps.notes.pdf_utils import generate_bulletin_pdf
from django.urls import reverse


def get_session_or_warning(request):
    """Récupère la session active ou la plus récente. Retourne None si aucune."""
    session = SessionVacances.objects.filter(est_active=True).first()
    if not session:
        session = SessionVacances.objects.order_by('-date_debut').first()
    if not session:
        messages.warning(
            request,
            '⚠️ Aucune session de vacances créée. '
            'Allez dans <a href="/admin/core/sessionvacances/add/" class="alert-link">l\'administration</a> '
            'pour créer une session avant d\'utiliser cette page.'
        )
        return None
    return session


@login_required
@staff_comite_required
def config_bulletins(request):
    """Configuration de l'ouverture/fermeture de saisie et génération."""
    session = get_session_or_warning(request)
    if not session:
        return render(request, 'comite/notes/config_bulletins.html', {'session': None, 'niveaux_config': []})

    niveaux = Niveau.objects.all().order_by('cycle', 'nom')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_config':
            for niveau in niveaux:
                config, created = BulletinConfig.objects.get_or_create(
                    niveau=niveau,
                    session=session,
                )
                config.saisie_ouverte = request.POST.get(f'saisie_{niveau.id}') == 'on'
                config.bulletin_generable = request.POST.get(f'bulletin_{niveau.id}') == 'on'
                config.save()
            messages.success(request, 'Configuration enregistrée avec succès.')
            return redirect('notes_comite:config_bulletins')

        elif action == 'generate_bulletins':
            niveau_id = request.POST.get('niveau_id')
            message_directeur = request.POST.get('message_directeur', '').strip()
            eleves_ids = request.POST.getlist('eleves_ids')

            if not eleves_ids:
                messages.warning(request, 'Aucun élève sélectionné.')
                return redirect('notes_comite:config_bulletins')

            inscriptions = Inscription.objects.filter(
                id__in=eleves_ids,
                session=session
            ).select_related('niveau')

            generated = []
            for inscription in inscriptions:
                notes_qs = Note.objects.filter(
                    inscription=inscription,
                    session=session
                ).select_related('matiere')

                notes_data = []
                for note in notes_qs:
                    notes_data.append({
                        'matiere': note.matiere.nom,
                        'note': note.note,
                        'coefficient': note.coefficient,
                    })

                if notes_data:
                    pdf_buffer = generate_bulletin_pdf(
                        inscription, notes_data, session,
                        message_directeur=message_directeur
                    )
                    from django.core.files.base import ContentFile
                    filename = f"bulletin_{inscription.nom_eleve}_{inscription.prenom_eleve}_{session.annee}.pdf".replace(' ', '_')
                    bulletin = BulletinGenere(
                        inscription=inscription,
                        session=session,
                        genere_par=request.user,
                    )
                    bulletin.fichier_pdf.save(filename, ContentFile(pdf_buffer.getvalue()), save=True)
                    generated.append(inscription)

            messages.success(request, f'{len(generated)} bulletin(s) généré(s) avec succès.')
            return redirect('notes_comite:config_bulletins')

    # Récupérer les configurations existantes
    configs = {
        (c.niveau_id, c.session_id): c
        for c in BulletinConfig.objects.filter(session=session)
    }

    niveaux_config = []
    for niveau in niveaux:
        config = configs.get((niveau.id, session.id))
        saisie_ouverte = config.saisie_ouverte if config else False
        bulletin_generable = config.bulletin_generable if config else False

        effectif = Inscription.objects.filter(
            niveau=niveau, session=session
        ).count()
        notes_present = Note.objects.filter(
            session=session,
            inscription__niveau=niveau
        ).values('inscription').distinct().count()

        niveaux_config.append({
            'niveau': niveau,
            'saisie_ouverte': saisie_ouverte,
            'bulletin_generable': bulletin_generable,
            'effectif': effectif,
            'notes_present': notes_present,
            'config': config,
        })

    context = {
        'session': session,
        'niveaux_config': niveaux_config,
    }
    return render(request, 'comite/notes/config_bulletins.html', context)


@login_required
@staff_comite_required
def liste_eleves_notes(request, niveau_id):
    """Liste des élèves d'une classe avec leurs notes pour génération."""
    session = get_session_or_warning(request)
    niveau = get_object_or_404(Niveau, pk=niveau_id)

    if not session:
        return render(request, 'comite/notes/liste_eleves.html', {
            'niveau': niveau, 'session': None, 'inscriptions': []
        })

    statut_paiement = request.GET.get('paiement', '')

    inscriptions = Inscription.objects.filter(
        niveau=niveau,
        session=session,
    ).order_by('nom_eleve', 'prenom_eleve')

    if statut_paiement:
        inscriptions = inscriptions.filter(statut_paiement=statut_paiement)

    inscriptions_data = []
    for ins in inscriptions:
        notes_qs = Note.objects.filter(
            inscription=ins, session=session
        ).select_related('matiere')

        total_pondere = 0
        total_coef = 0
        for note in notes_qs:
            coef = float(note.coefficient)
            total_pondere += float(note.note) * coef
            total_coef += coef

        moyenne = round(total_pondere / total_coef, 2) if total_coef > 0 else None

        inscriptions_data.append({
            'inscription': ins,
            'nb_notes': notes_qs.count(),
            'moyenne': moyenne,
            'total_notes': notes_qs.aggregate(total=Sum('note'))['total'],
        })

    context = {
        'niveau': niveau,
        'session': session,
        'inscriptions': inscriptions_data,
        'statut_paiement': statut_paiement,
        'filtres_paiement': ['', 'PAYE', 'PARTIEL', 'IMPAYE'],
    }
    return render(request, 'comite/notes/liste_eleves.html', context)


@login_required
@staff_comite_required
def telecharger_bulletin(request, bulletin_id):
    """Télécharger un bulletin PDF déjà généré."""
    bulletin = get_object_or_404(BulletinGenere, pk=bulletin_id)
    response = HttpResponse(
        bulletin.fichier_pdf.read(),
        content_type='application/pdf'
    )
    filename = bulletin.fichier_pdf.name.split('/')[-1]
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
@staff_comite_required
def bulletins_generes(request):
    """Liste des bulletins déjà générés."""
    session = get_session_or_warning(request)
    if not session:
        return render(request, 'comite/notes/bulletins_generes.html', {
            'session': None, 'bulletins': [], 'niveaux': [], 'niveau_id': ''
        })

    niveau_id = request.GET.get('niveau', '')

    bulletins = BulletinGenere.objects.filter(
        session=session
    ).select_related(
        'inscription__niveau', 'genere_par'
    ).order_by('-genere_le')

    if niveau_id:
        bulletins = bulletins.filter(inscription__niveau_id=niveau_id)

    niveaux = Niveau.objects.all()

    context = {
        'session': session,
        'bulletins': bulletins,
        'niveaux': niveaux,
        'niveau_id': niveau_id,
    }
    return render(request, 'comite/notes/bulletins_generes.html', context)


@login_required
@staff_comite_required
def coefficients_matiere(request, niveau_id):
    """Gestion des coefficients pour une classe."""
    niveau = get_object_or_404(Niveau, pk=niveau_id)
    from apps.emploi_du_temps.models import Matiere

    if request.method == 'POST':
        matiere_id = request.POST.get('matiere_id')
        coefficient = request.POST.get('coefficient')

        if matiere_id and coefficient:
            try:
                coef_dec = Decimal(coefficient)
                if coef_dec < 0.5 or coef_dec > 10:
                    messages.error(request, 'Le coefficient doit être entre 0.5 et 10.')
                else:
                    CoefficientMatiere.objects.update_or_create(
                        matiere_id=matiere_id,
                        niveau=niveau,
                        defaults={'coefficient': coef_dec}
                    )
                    messages.success(request, 'Coefficient enregistré.')
            except (ValueError, Decimal.InvalidOperation):
                messages.error(request, 'Coefficient invalide.')
        return redirect('notes_comite:coefficients', niveau_id=niveau_id)

    coefficients = {
        c.matiere_id: c
        for c in CoefficientMatiere.objects.filter(niveau=niveau)
    }

    matieres = Matiere.objects.all().order_by('nom')

    matieres_data = []
    for m in matieres:
        matieres_data.append({
            'matiere': m,
            'coefficient': coefficients.get(m.id),
        })

    context = {
        'niveau': niveau,
        'matieres': matieres_data,
    }
    return render(request, 'comite/notes/coefficients.html', context)


@login_required
@staff_comite_required
def saisie_notes_admin(request, niveau_id):
    """Permet au comité de saisir/modifier les notes des élèves (toutes matières)."""
    session = get_session_or_warning(request)
    niveau = get_object_or_404(Niveau, pk=niveau_id)
    if not session:
        return redirect('notes_comite:config_bulletins')

    from apps.emploi_du_temps.models import Matiere, EmploiDuTemps
    from apps.enseignants.models import Enseignant

    # Toutes les matières qui ont des créneaux pour ce niveau dans cette session
    matieres_ids = list(dict.fromkeys(
        EmploiDuTemps.objects.filter(
            session=session, niveau=niveau
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
        enseignant_id = request.POST.get('enseignant_id')
        if not matiere_id or int(matiere_id) not in matieres_ids:
            messages.error(request, 'Matière invalide.')
            return redirect('notes_comite:saisie_notes_admin', niveau_id=niveau_id)

        matiere_id = int(matiere_id)
        matiere = get_object_or_404(Matiere, pk=matiere_id)

        # Si aucun enseignant sélectionné, on prend le premier qui enseigne cette matière dans ce niveau
        if enseignant_id:
            enseignant = get_object_or_404(Enseignant, pk=enseignant_id)
        else:
            premier_creneau = EmploiDuTemps.objects.filter(
                session=session, niveau=niveau, matiere=matiere
            ).first()
            if not premier_creneau:
                messages.error(request, f'Aucun enseignant trouvé pour {matiere.nom} dans ce niveau.')
                return redirect('notes_comite:saisie_notes_admin', niveau_id=niveau_id)
            enseignant = premier_creneau.enseignant

        notes_enregistrees = 0
        for eleve in eleves:
            note_val = request.POST.get(f'note_{eleve.id}', '').strip()
            if note_val:
                try:
                    note_dec = Decimal(note_val)
                    if note_dec < 0 or note_dec > 20:
                        messages.warning(request, f"Note de {eleve.nom_eleve} ignorée (doit être 0-20).")
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
                    messages.warning(request, f"Note invalide pour {eleve.nom_eleve}.")

        messages.success(request, f'{notes_enregistrees} note(s) enregistrée(s) pour {matiere.nom}.')
        return redirect(f'{reverse("notes_comite:saisie_notes_admin", args=[niveau_id])}?matiere={matiere_id}')

    # GET
    matiere_active = None
    matiere_active_id = request.GET.get('matiere')
    if matiere_active_id and int(matiere_active_id) in matieres_ids:
        matiere_active = get_object_or_404(Matiere, pk=int(matiere_active_id))

    # Enseignants disponibles pour ce niveau
    enseignants = Enseignant.objects.filter(
        creneaux__session=session, creneaux__niveau=niveau
    ).distinct()

    notes_toutes = Note.objects.filter(
        inscription__in=eleves, matiere_id__in=matieres_ids,
        session=session
    ).select_related('matiere', 'enseignant')

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
        'niveau': niveau, 'session': session, 'matieres': matieres_objs,
        'matiere_active': matiere_active, 'coefficients': coeffs,
        'eleves_data': eleves_data, 'enseignants': enseignants,
        'count_notes_matiere_active': count_matiere_active,
    }
    return render(request, 'comite/notes/saisie_notes_admin.html', context)


@login_required
@staff_comite_required
def generer_tous_bulletins(request):
    """Génère les bulletins pour TOUS les élèves PAYÉS de toutes les classes."""
    session = get_session_or_warning(request)
    if not session:
        return redirect('notes_comite:config_bulletins')

    message_directeur = request.POST.get('message_directeur', '').strip()

    inscriptions = Inscription.objects.filter(
        session=session, statut_paiement='PAYE'
    ).select_related('niveau')

    generated = 0
    skipped_no_notes = 0
    for inscription in inscriptions:
        notes_qs = Note.objects.filter(
            inscription=inscription, session=session
        ).select_related('matiere')

        notes_data = []
        for note in notes_qs:
            notes_data.append({
                'matiere': note.matiere.nom,
                'note': note.note,
                'coefficient': note.coefficient,
            })

        if notes_data:
            pdf_buffer = generate_bulletin_pdf(
                inscription, notes_data, session,
                message_directeur=message_directeur
            )
            from django.core.files.base import ContentFile
            filename = f"bulletin_{inscription.nom_eleve}_{inscription.prenom_eleve}_{session.annee}.pdf".replace(' ', '_')
            bulletin = BulletinGenere(
                inscription=inscription, session=session, genere_par=request.user,
            )
            bulletin.fichier_pdf.save(filename, ContentFile(pdf_buffer.getvalue()), save=True)
            generated += 1
        else:
            skipped_no_notes += 1

    if generated:
        messages.success(
            request,
            f'✅ {generated} bulletin(s) généré(s) avec succès pour les élèves payés.'
            + (f' {skipped_no_notes} élève(s) sans notes ignoré(s).' if skipped_no_notes else '')
        )
    else:
        messages.warning(request, 'Aucun bulletin généré. Vérifiez que des élèves ont le statut "Payé" et ont des notes.')
    return redirect('notes_comite:config_bulletins')


@login_required
@staff_comite_required
def liste_eleves_generation(request, niveau_id):
    """Page pour sélectionner les élèves d'une classe et générer les bulletins."""
    session = get_session_or_warning(request)
    niveau = get_object_or_404(Niveau, pk=niveau_id)

    if not session:
        return render(request, 'comite/notes/generer_bulletins.html', {
            'niveau': niveau, 'session': None, 'inscriptions': []
        })

    statut_paiement = request.GET.get('paiement', '')

    inscriptions = Inscription.objects.filter(
        niveau=niveau,
        session=session,
    ).order_by('nom_eleve', 'prenom_eleve')

    if statut_paiement:
        inscriptions = inscriptions.filter(statut_paiement=statut_paiement)

    inscriptions_data = []
    for ins in inscriptions:
        notes_qs = Note.objects.filter(
            inscription=ins, session=session
        ).select_related('matiere')

        total_pondere = 0
        total_coef = 0
        notes_detail = []
        for note in notes_qs:
            coef = float(note.coefficient)
            total_pondere += float(note.note) * coef
            total_coef += coef
            notes_detail.append({
                'matiere': note.matiere.nom,
                'note': note.note,
                'coefficient': coef,
                'note_ponderee': round(float(note.note) * coef, 1),
            })

        moyenne = round(total_pondere / total_coef, 2) if total_coef > 0 else None

        from apps.notes.pdf_utils import mention_from_moyenne
        mention = mention_from_moyenne(moyenne) if moyenne else ''

        inscriptions_data.append({
            'id': ins.id,
            'inscription': ins,
            'nb_notes': notes_qs.count(),
            'moyenne': moyenne,
            'mention': mention,
            'notes_detail': notes_detail,
        })

    context = {
        'niveau': niveau,
        'session': session,
        'inscriptions': inscriptions_data,
        'statut_paiement': statut_paiement,
        'filtres_paiement': ['', 'PAYE', 'PARTIEL', 'IMPAYE'],
    }
    return render(request, 'comite/notes/generer_bulletins.html', context)
