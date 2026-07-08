from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from apps.accounts.decorators import enseignant_required
from apps.core.models import SessionVacances
from apps.emploi_du_temps.models import EmploiDuTemps
from apps.finances.models import Salaire
from apps.finances.pdf_utils import generate_bulletin_salaire


@login_required
@enseignant_required
def dashboard(request):
    enseignant = request.user.enseignant

    # Active session
    session = SessionVacances.objects.filter(est_active=True).first()

    # Taux de presence: (PRESENT + RETARD) / total * 100
    taux_presence = 0
    if session:
        total_presences = enseignant.presences.filter(
            creneau__session=session
        ).count()
        if total_presences > 0:
            presences_ok = enseignant.presences.filter(
                creneau__session=session,
                statut__in=['PRESENT', 'RETARD']
            ).count()
            taux_presence = round((presences_ok / total_presences) * 100, 1)

    # Heures effectuees from Salaire for active session
    heures_effectuees = 0
    if session:
        salaire = Salaire.objects.filter(
            enseignant=enseignant,
            session=session
        ).first()
        if salaire:
            heures_effectuees = salaire.nombre_heures_effectuees

    # Solde salaire: sum of (montant_brut - montant_deja_verse) for all salaires
    salaires = Salaire.objects.filter(enseignant=enseignant)
    solde_salaire = sum(s.solde_restant for s in salaires)

    # This week's emploi du temps
    aujourdhui = timezone.now().date()
    lundi = aujourdhui - timezone.timedelta(days=aujourdhui.weekday())
    jours_semaine = ['LUNDI', 'MARDI', 'MERCREDI', 'JEUDI', 'VENDREDI']

    emploi_du_temps = EmploiDuTemps.objects.filter(
        enseignant=enseignant,
        session=session,
    ).select_related('matiere', 'niveau').order_by('jour', 'heure_debut')

    context = {
        'enseignant': enseignant,
        'taux_presence': taux_presence,
        'heures_effectuees': heures_effectuees,
        'solde_salaire': solde_salaire,
        'emploi_du_temps': emploi_du_temps,
        'session': session,
        'jours_semaine': jours_semaine,
        'lundi': lundi,
    }
    return render(request, 'enseignant/dashboard.html', context)


@login_required
@enseignant_required
def mon_qrcode(request):
    enseignant = request.user.enseignant
    return render(request, 'enseignant/mon_qrcode.html', {'enseignant': enseignant})


@login_required
@enseignant_required
def mes_presences(request):
    enseignant = request.user.enseignant
    presences = enseignant.presences.select_related(
        'creneau__matiere', 'creneau__niveau', 'creneau__session', 'valide_par'
    ).order_by('-date', '-heure_scan')

    context = {
        'enseignant': enseignant,
        'presences': presences,
    }
    return render(request, 'enseignant/presences.html', context)


@login_required
@enseignant_required
def mes_salaires(request):
    enseignant = request.user.enseignant
    salaires = enseignant.salaires.select_related('session').order_by('-date_calcul')

    context = {
        'enseignant': enseignant,
        'salaires': salaires,
    }
    return render(request, 'enseignant/salaires.html', context)


@login_required
@enseignant_required
def bulletin_pdf(request, salaire_id):
    enseignant = request.user.enseignant
    salaire = get_object_or_404(
        Salaire.objects.select_related('session', 'enseignant__user'),
        pk=salaire_id,
        enseignant=enseignant
    )

    buffer = generate_bulletin_salaire(salaire)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"bulletin_salaire_{salaire.enseignant}_{salaire.session.nom.replace(' ', '_')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
@enseignant_required
def profil(request):
    user = request.user
    enseignant = request.user.enseignant

    if request.method == 'POST':
        telephone = request.POST.get('telephone', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        updated = False

        # Update telephone
        if telephone:
            user.telephone = telephone
            user.save(update_fields=['telephone'])
            updated = True
            messages.success(request, 'Votre numéro de téléphone a été mis à jour.')

        # Update password only if provided
        if new_password:
            if new_password != confirm_password:
                messages.error(request, 'Les mots de passe ne correspondent pas.')
            elif len(new_password) < 6:
                messages.error(request, 'Le mot de passe doit contenir au moins 6 caractères.')
            else:
                user.set_password(new_password)
                user.save(update_fields=['password'])
                update_session_auth_hash(request, user)
                updated = True
                messages.success(request, 'Votre mot de passe a été mis à jour avec succès.')

        if not updated and not new_password:
            messages.info(request, 'Aucune modification apportée.')

        return redirect('enseignant:profil')

    context = {
        'enseignant': enseignant,
        'user': user,
    }
    return render(request, 'enseignant/profil.html', context)
