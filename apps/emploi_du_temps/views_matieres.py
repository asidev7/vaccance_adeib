from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import secretaire_required
from apps.emploi_du_temps.models import Matiere


@login_required
@secretaire_required
def liste(request):
    matieres = Matiere.objects.all()
    return render(request, 'comite/matieres/list.html', {'matieres': matieres})


@login_required
@secretaire_required
def ajouter(request):
    if request.method == 'POST':
        Matiere.objects.create(
            nom=request.POST.get('nom', '').strip(),
            niveau_concerne=request.POST.get('niveau_concerne'),
            couleur_badge=request.POST.get('couleur_badge', '#0048AE'),
        )
        messages.success(request, 'Matière ajoutée.')
        return redirect('matieres:liste')
    return render(request, 'comite/matieres/form.html')


@login_required
@secretaire_required
def modifier(request, id):
    matiere = get_object_or_404(Matiere, pk=id)
    if request.method == 'POST':
        matiere.nom = request.POST.get('nom', '').strip()
        matiere.niveau_concerne = request.POST.get('niveau_concerne')
        matiere.couleur_badge = request.POST.get('couleur_badge', '#0048AE')
        matiere.save()
        messages.success(request, 'Matière modifiée.')
        return redirect('matieres:liste')
    return render(request, 'comite/matieres/form.html', {'matiere': matiere})


@login_required
@secretaire_required
def supprimer(request, id):
    matiere = get_object_or_404(Matiere, pk=id)
    matiere.delete()
    messages.success(request, 'Matière supprimée.')
    return redirect('matieres:liste')
