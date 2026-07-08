from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import secretaire_required
from apps.emploi_du_temps.models import Niveau


@login_required
@secretaire_required
def liste(request):
    niveaux = Niveau.objects.all()
    return render(request, 'comite/niveaux/list.html', {'niveaux': niveaux})


@login_required
@secretaire_required
def ajouter(request):
    if request.method == 'POST':
        Niveau.objects.create(
            nom=request.POST.get('nom', '').strip(),
            cycle=request.POST.get('cycle'),
        )
        messages.success(request, 'Niveau ajouté.')
        return redirect('niveaux:liste')
    return render(request, 'comite/niveaux/form.html')


@login_required
@secretaire_required
def modifier(request, id):
    niveau = get_object_or_404(Niveau, pk=id)
    if request.method == 'POST':
        niveau.nom = request.POST.get('nom', '').strip()
        niveau.cycle = request.POST.get('cycle')
        niveau.save()
        messages.success(request, 'Niveau modifié.')
        return redirect('niveaux:liste')
    return render(request, 'comite/niveaux/form.html', {'niveau': niveau})


@login_required
@secretaire_required
def supprimer(request, id):
    niveau = get_object_or_404(Niveau, pk=id)
    niveau.delete()
    messages.success(request, 'Niveau supprimé.')
    return redirect('niveaux:liste')
