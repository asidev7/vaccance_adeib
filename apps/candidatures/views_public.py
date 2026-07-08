from django.shortcuts import render, redirect

from apps.candidatures.models import CandidatureEnseignant


def formulaire(request):
    return redirect('core:accueil')


def suivi(request):
    candidature = None

    if request.method == 'POST':
        telephone = request.POST.get('telephone', '').strip()
        if telephone:
            candidature = CandidatureEnseignant.objects.filter(
                telephone=telephone
            ).first()

    context = {
        'candidature': candidature,
    }
    return render(request, 'public/suivi_candidature.html', context)
