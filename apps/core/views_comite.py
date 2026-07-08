from datetime import date
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from apps.accounts.decorators import staff_comite_required
from apps.inscriptions.models import Inscription
from apps.candidatures.models import CandidatureEnseignant
from apps.enseignants.models import Presence
from apps.inscriptions.models import Paiement
from apps.finances.models import Depense


@login_required
@staff_comite_required
def dashboard(request):
    today = date.today()

    # Stats
    inscriptions_aujourdhui = Inscription.objects.filter(date_inscription__date=today).count()
    candidatures_en_attente = CandidatureEnseignant.objects.filter(statut='EN_ATTENTE').count()

    # Presence rate: PRESENT + RETARD / total presences
    total_presences = Presence.objects.count()
    if total_presences > 0:
        presences_effectives = Presence.objects.filter(statut__in=['PRESENT', 'RETARD']).count()
        taux_presence = round((presences_effectives / total_presences) * 100, 1)
    else:
        taux_presence = 0

    # Solde: total confirmed Paiement - total Depense
    total_recettes = Paiement.objects.filter(statut='CONFIRME').aggregate(
        total=Sum('montant')
    )['total'] or 0
    total_depenses = Depense.objects.aggregate(total=Sum('montant'))['total'] or 0
    solde = total_recettes - total_depenses

    stats = {
        'inscriptions_aujourdhui': inscriptions_aujourdhui,
        'candidatures_en_attente': candidatures_en_attente,
        'taux_presence': taux_presence,
        'solde': solde,
        'total_recettes': total_recettes,
        'total_depenses': total_depenses,
    }

    # Recent items
    inscriptions_recentes = Inscription.objects.select_related('niveau').order_by('-date_inscription')[:5]
    candidatures_recentes = CandidatureEnseignant.objects.order_by('-date_soumission')[:5]

    context = {
        'stats': stats,
        'inscriptions_recentes': inscriptions_recentes,
        'candidatures_recentes': candidatures_recentes,
    }
    return render(request, 'comite/dashboard.html', context)
