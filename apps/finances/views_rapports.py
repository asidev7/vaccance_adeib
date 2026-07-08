from datetime import datetime
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum
from openpyxl import Workbook
from apps.accounts.decorators import tresorier_required
from apps.core.models import SessionVacances
from apps.inscriptions.models import Paiement, Inscription
from apps.finances.models import Depense
from apps.finances.pdf_utils import generate_bilan_financier
from apps.enseignants.models import Presence


@login_required
@tresorier_required
def index(request):
    sessions = SessionVacances.objects.all()
    return render(request, 'comite/rapports/index.html', {'sessions': sessions})


@login_required
@tresorier_required
def bilan_pdf(request):
    session_id = request.GET.get('session')
    if session_id:
        session = get_object_or_404(SessionVacances, pk=session_id)
    else:
        session = SessionVacances.objects.filter(est_active=True).first()

    if not session:
        messages.error(request, 'Aucune session trouvée.')
        return redirect('rapports:index')

    # Calculate totals
    recettes = Paiement.objects.filter(
        statut='CONFIRME',
        inscription__session=session,
    ).aggregate(total=Sum('montant'))['total'] or 0

    depenses = Depense.objects.filter(
        date_depense__gte=session.date_debut,
        date_depense__lte=session.date_fin,
    ).aggregate(total=Sum('montant'))['total'] or 0

    solde = recettes - depenses

    # Detailed recettes
    details_recettes = []
    inscriptions = Inscription.objects.filter(session=session)
    for ins in inscriptions:
        total_paye = ins.paiements.filter(statut='CONFIRME').aggregate(
            total=Sum('montant')
        )['total'] or 0
        if total_paye > 0:
            details_recettes.append({
                'libelle': f'{ins.nom_eleve} {ins.prenom_eleve}',
                'montant': total_paye,
            })

    # Detailed depenses
    details_depenses = []
    for d in Depense.objects.filter(
        date_depense__gte=session.date_debut,
        date_depense__lte=session.date_fin,
    ):
        details_depenses.append({
            'libelle': d.libelle,
            'categorie': d.get_categorie_display(),
            'montant': d.montant,
        })

    buffer = generate_bilan_financier(session, recettes, depenses, solde, details_recettes, details_depenses)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="bilan_{session.nom.replace(" ", "_")}.pdf"'
    return response


@login_required
@tresorier_required
def presences_excel(request):
    session_id = request.GET.get('session')
    if session_id:
        session = get_object_or_404(SessionVacances, pk=session_id)
    else:
        session = SessionVacances.objects.filter(est_active=True).first()

    if not session:
        messages.error(request, 'Aucune session trouvée.')
        return redirect('rapports:index')

    wb = Workbook()
    ws = wb.active
    ws.title = 'Présences'

    # Headers
    headers = ['Enseignant', 'Date', 'Jour', 'Créneau', 'Matière', 'Niveau', 'Statut', 'Heure scan', 'Validé par']
    ws.append(headers)

    # Data
    presences = Presence.objects.filter(
        creneau__session=session,
    ).select_related('enseignant__user', 'creneau__matiere', 'creneau__niveau', 'valide_par').order_by('date', 'enseignant')

    for p in presences:
        ws.append([
            str(p.enseignant),
            p.date.strftime('%d/%m/%Y'),
            p.creneau.get_jour_display(),
            f'{p.creneau.heure_debut.strftime("%H:%M")}–{p.creneau.heure_fin.strftime("%H:%M")}',
            p.creneau.matiere.nom,
            p.creneau.niveau.nom,
            p.get_statut_display(),
            p.heure_scan.strftime('%H:%M') if p.heure_scan else '',
            p.valide_par.get_full_name() if p.valide_par else '',
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="presences_{session.nom.replace(" ", "_")}.xlsx"'
    wb.save(response)
    return response
