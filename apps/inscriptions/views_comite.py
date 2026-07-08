from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from apps.accounts.decorators import secretaire_required
from apps.core.models import SessionVacances
from apps.emploi_du_temps.models import Matiere, Niveau
from apps.inscriptions.models import Inscription, Paiement


@login_required
@secretaire_required
def ajouter(request):
    """Ajouter une inscription élève avec frais automatique selon le niveau."""
    session_active = SessionVacances.objects.filter(est_active=True).first()
    niveaux = Niveau.objects.all()
    matieres = Matiere.objects.all()

    if not session_active:
        messages.error(request, "Aucune session active. Impossible d'ajouter une inscription.")
        return redirect('inscriptions_comite:liste_comite')

    if request.method == 'POST':
        nom_eleve = request.POST.get('nom_eleve', '').strip()
        prenom_eleve = request.POST.get('prenom_eleve', '').strip()
        date_naissance = request.POST.get('date_naissance', '')
        niveau_id = request.POST.get('niveau', '')
        nom_parent = request.POST.get('nom_parent', '').strip()
        telephone_parent = request.POST.get('telephone_parent', '').strip()
        matieres_ids = request.POST.getlist('matieres')
        montant_paye = request.POST.get('montant_paye', '0').strip()
        methode_paiement = request.POST.get('methode_paiement', 'ESPECES')

        # Validation
        errors = []
        if not nom_eleve: errors.append('Nom de l\'élève requis.')
        if not prenom_eleve: errors.append('Prénom de l\'élève requis.')
        if not date_naissance: errors.append('Date de naissance requise.')
        if not niveau_id: errors.append('Niveau requis.')
        if not nom_parent: errors.append('Nom du parent requis.')
        if not telephone_parent: errors.append('Téléphone du parent requis.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'comite/inscriptions/ajouter.html', {
                'niveaux': niveaux, 'matieres': matieres,
                'session_active': session_active,
                'form_data': request.POST,
            })

        niveau = get_object_or_404(Niveau, pk=niveau_id)
        frais = niveau.frais_inscription

        try:
            montant_paye = int(montant_paye) if montant_paye else 0
        except ValueError:
            montant_paye = 0

        if montant_paye > frais:
            montant_paye = frais
        if montant_paye < 0:
            montant_paye = 0

        if montant_paye >= frais:
            statut_paiement = 'PAYE'
        elif montant_paye > 0:
            statut_paiement = 'PARTIEL'
        else:
            statut_paiement = 'IMPAYE'

        inscription = Inscription.objects.create(
            nom_eleve=nom_eleve,
            prenom_eleve=prenom_eleve,
            date_naissance=date_naissance,
            niveau=niveau,
            nom_parent=nom_parent,
            telephone_parent=telephone_parent,
            session=session_active,
            montant_du=frais,
            montant_paye=montant_paye,
            statut_paiement=statut_paiement,
        )
        inscription.matieres_choisies.set(matieres_ids)

        # Créer un paiement si un montant a été versé
        if montant_paye > 0:
            Paiement.objects.create(
                inscription=inscription,
                montant=montant_paye,
                methode=methode_paiement,
                statut='CONFIRME',
                enregistre_par=request.user,
            )

        messages.success(
            request,
            f'✅ {nom_eleve} {prenom_eleve} inscrit(e) en {niveau.nom}. '
            f'Frais : {frais} FCFA | Payé : {montant_paye} FCFA.'
        )
        return redirect('inscriptions_comite:detail_comite', id=inscription.id)

    return render(request, 'comite/inscriptions/ajouter.html', {
        'niveaux': niveaux,
        'matieres': matieres,
        'session_active': session_active,
    })


@login_required
@secretaire_required
def liste(request):
    inscriptions = Inscription.objects.select_related('niveau', 'session').all()

    # Filters
    q = request.GET.get('q', '').strip()
    if q:
        inscriptions = inscriptions.filter(
            Q(nom_eleve__icontains=q) | Q(nom_parent__icontains=q)
        )

    niveau_filter = request.GET.get('niveau', '').strip()
    if niveau_filter:
        inscriptions = inscriptions.filter(niveau_id=niveau_filter)

    statut_filter = request.GET.get('statut', '').strip()
    if statut_filter:
        inscriptions = inscriptions.filter(statut_paiement=statut_filter)

    inscriptions = inscriptions.order_by('-date_inscription')

    from apps.emploi_du_temps.models import Niveau
    niveaux = Niveau.objects.all()

    context = {
        'inscriptions': inscriptions,
        'niveaux': niveaux,
        'q': q,
        'niveau_filter': niveau_filter,
        'statut_filter': statut_filter,
    }
    return render(request, 'comite/inscriptions/list.html', context)


@login_required
@secretaire_required
def detail(request, id):
    inscription = get_object_or_404(Inscription.objects.select_related('niveau', 'session'), pk=id)
    paiements = inscription.paiements.all()
    reste = inscription.montant_du - inscription.montant_paye

    context = {
        'inscription': inscription,
        'paiements': paiements,
        'reste': reste,
    }
    return render(request, 'comite/inscriptions/detail.html', context)


@login_required
@secretaire_required
def paiement_ajout(request, id):
    inscription = get_object_or_404(Inscription, pk=id)

    if request.method == 'POST':
        montant = request.POST.get('montant', '').strip()
        methode = request.POST.get('methode', 'ESPECES')
        reference = request.POST.get('reference_fedapay', '').strip()

        try:
            montant = int(montant)
        except (ValueError, TypeError):
            messages.error(request, 'Le montant doit être un nombre valide.')
            return redirect('inscriptions_comite:detail_comite', id=inscription.id)

        if montant <= 0:
            messages.error(request, 'Le montant doit être supérieur à 0.')
            return redirect('inscriptions_comite:detail_comite', id=inscription.id)

        Paiement.objects.create(
            inscription=inscription,
            montant=montant,
            methode=methode,
            reference_fedapay=reference if reference else None,
            statut='CONFIRME',
            enregistre_par=request.user,
        )

        messages.success(request, f'Paiement de {montant} FCFA enregistré avec succès.')
        return redirect('inscriptions_comite:detail_comite', id=inscription.id)

    # GET request
    context = {
        'inscription': inscription,
    }
    return render(request, 'comite/inscriptions/paiement_form.html', context)
