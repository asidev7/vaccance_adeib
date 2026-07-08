from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum
from apps.accounts.decorators import tresorier_required
from apps.core.models import SessionVacances
from apps.enseignants.models import Enseignant, Presence
from apps.finances.models import Salaire, VersementSalaire
from apps.finances.pdf_utils import generate_bulletin_salaire


@login_required
@tresorier_required
def liste(request):
    salaires = Salaire.objects.select_related(
        'enseignant__user', 'session'
    ).order_by('-date_calcul')

    return render(request, 'comite/salaires/list.html', {'salaires': salaires})


@login_required
@tresorier_required
def calculer(request):
    """Calculate salaries for all teachers based on valid presences in the active session."""
    session_active = SessionVacances.objects.filter(est_active=True).first()
    if not session_active:
        messages.error(request, 'Aucune session active.')
        return redirect('salaires:liste')

    enseignants = Enseignant.objects.filter(est_actif=True)
    created = 0
    updated = 0

    for enseignant in enseignants:
        # Count hours from presences with status PRESENT or RETARD
        presences = Presence.objects.filter(
            enseignant=enseignant,
            creneau__session=session_active,
            statut__in=['PRESENT', 'RETARD'],
        ).select_related('creneau')

        total_minutes = 0
        for p in presences:
            debut = p.creneau.heure_debut
            fin = p.creneau.heure_fin
            today = datetime.combine(p.date, debut)
            end = datetime.combine(p.date, fin)
            delta = (end - today).total_seconds() / 60
            total_minutes += delta

        heures = round(total_minutes / 60, 1)

        if heures > 0:
            taux = enseignant.taux_horaire
            brut = round(heures * float(taux))

            salaire, is_new = Salaire.objects.update_or_create(
                utilisateur=enseignant.user,
                session=session_active,
                defaults={
                    'enseignant': enseignant,
                    'type_personnel': 'ENSEIGNANT',
                    'nombre_heures_effectuees': heures,
                    'taux_horaire': taux,
                    'montant_brut': brut,
                },
            )
            if is_new:
                created += 1
            else:
                updated += 1

    messages.success(
        request,
        f'Salaires calculés : {created} créé(s), {updated} mis à jour. '
        f'Seuls les enseignants avec des heures effectuées sont inclus.'
    )
    return redirect('salaires:liste')


@login_required
@tresorier_required
def detail(request, id):
    salaire = get_object_or_404(
        Salaire.objects.select_related('enseignant__user', 'session').prefetch_related('versements'),
        pk=id
    )
    return render(request, 'comite/salaires/detail.html', {'salaire': salaire})


@login_required
@tresorier_required
def versement_ajout(request, id):
    salaire = get_object_or_404(Salaire, pk=id)

    if request.method == 'POST':
        montant = request.POST.get('montant', '').strip()
        mode = request.POST.get('mode_paiement', 'ESPECES')

        try:
            montant = int(montant)
        except (ValueError, TypeError):
            messages.error(request, 'Montant invalide.')
            return redirect('salaires:detail', id=salaire.id)

        if montant <= 0:
            messages.error(request, 'Le montant doit être supérieur à 0.')
            return redirect('salaires:detail', id=salaire.id)

        if montant > salaire.solde_restant:
            messages.error(request, f'Le montant dépasse le solde restant ({salaire.solde_restant} FCFA).')
            return redirect('salaires:detail', id=salaire.id)

        VersementSalaire.objects.create(
            salaire=salaire,
            montant=montant,
            mode_paiement=mode,
            verse_par=request.user,
        )

        messages.success(request, f'Versement de {montant} FCFA enregistré.')
        return redirect('salaires:detail', id=salaire.id)

    return render(request, 'comite/salaires/detail.html', {'salaire': salaire})


@login_required
@tresorier_required
def bulletin_pdf(request, id):
    salaire = get_object_or_404(
        Salaire.objects.select_related('enseignant__user', 'utilisateur', 'session'),
        pk=id
    )

    buffer = generate_bulletin_salaire(salaire)
    nom = salaire.enseignant.user.get_full_name() if salaire.enseignant else salaire.utilisateur.get_full_name()
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"bulletin_salaire_{nom}_{salaire.session.nom.replace(' ', '_')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
