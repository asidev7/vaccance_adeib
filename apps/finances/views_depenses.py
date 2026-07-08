from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import tresorier_required
from apps.finances.models import Depense


@login_required
@tresorier_required
def liste(request):
    depenses = Depense.objects.all()
    filtre_cat = request.GET.get('categorie', '').strip()
    if filtre_cat:
        depenses = depenses.filter(categorie=filtre_cat)
    depenses = depenses.order_by('-date_depense')
    return render(request, 'comite/depenses/list.html', {
        'depenses': depenses,
        'filtre_cat': filtre_cat,
    })


@login_required
@tresorier_required
def ajouter(request):
    if request.method == 'POST':
        depense = Depense.objects.create(
            libelle=request.POST.get('libelle', '').strip(),
            categorie=request.POST.get('categorie'),
            montant=request.POST.get('montant'),
            date_depense=request.POST.get('date_depense'),
            enregistre_par=request.user,
        )
        if 'justificatif' in request.FILES:
            depense.justificatif = request.FILES['justificatif']
            depense.save(update_fields=['justificatif'])
        messages.success(request, 'Dépense enregistrée.')
        return redirect('depenses:liste')
    return render(request, 'comite/depenses/form.html')


@login_required
@tresorier_required
def modifier(request, id):
    depense = get_object_or_404(Depense, pk=id)
    if request.method == 'POST':
        depense.libelle = request.POST.get('libelle', '').strip()
        depense.categorie = request.POST.get('categorie')
        depense.montant = request.POST.get('montant')
        depense.date_depense = request.POST.get('date_depense')
        depense.save()
        if 'justificatif' in request.FILES:
            depense.justificatif = request.FILES['justificatif']
            depense.save(update_fields=['justificatif'])
        messages.success(request, 'Dépense modifiée.')
        return redirect('depenses:liste')
    return render(request, 'comite/depenses/form.html', {'depense': depense})
