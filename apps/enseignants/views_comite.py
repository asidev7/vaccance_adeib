from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from apps.accounts.decorators import staff_comite_required, admin_required
from apps.accounts.models import CustomUser
from apps.enseignants.models import Enseignant
from apps.emploi_du_temps.models import Matiere


@login_required
@staff_comite_required
def liste(request):
    enseignants = Enseignant.objects.select_related('user').all()
    context = {
        'enseignants': enseignants,
    }
    return render(request, 'comite/enseignants/list.html', context)


@login_required
@staff_comite_required
def detail(request, id):
    enseignant = get_object_or_404(
        Enseignant.objects.select_related('user').prefetch_related('matieres'),
        pk=id
    )
    presences_recentes = enseignant.presences.select_related('creneau').order_by('-date', '-heure_scan')[:20]

    context = {
        'enseignant': enseignant,
        'presences_recentes': presences_recentes,
    }
    return render(request, 'comite/enseignants/detail.html', context)


@login_required
@staff_comite_required
def desactiver(request, id):
    enseignant = get_object_or_404(Enseignant.objects.select_related('user'), pk=id)

    enseignant.est_actif = False
    enseignant.save(update_fields=['est_actif'])

    enseignant.user.est_actif = False
    enseignant.user.save(update_fields=['est_actif'])

    messages.warning(request, f"L'enseignant {enseignant} a été désactivé.")
    return redirect('enseignants_comite:liste_comite')


@login_required
@admin_required
def ajouter_enseignant(request):
    matieres = Matiere.objects.all().order_by('nom')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        telephone = request.POST.get('telephone', '').strip()
        email = request.POST.get('email', '').strip()
        taux_horaire = request.POST.get('taux_horaire', '')
        matieres_ids = request.POST.getlist('matieres')

        errors = []
        if not username:
            errors.append("Le nom d'utilisateur est requis.")
        if CustomUser.objects.filter(username=username).exists():
            errors.append("Ce nom d'utilisateur existe déjà.")
        if not last_name:
            errors.append("Le nom est requis.")
        if not first_name:
            errors.append("Le prénom est requis.")

        try:
            taux_horaire = int(taux_horaire) if taux_horaire else 1000
        except ValueError:
            errors.append("Le taux horaire doit être un nombre valide.")

        if errors:
            for error in errors:
                messages.error(request, error)
            context = {
                'matieres': matieres,
                'form_data': request.POST,
            }
            return render(request, 'comite/enseignants/ajouter.html', context)

        password = get_random_string(length=10)
        user = CustomUser.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            telephone=telephone,
            role=CustomUser.Role.ENSEIGNANT,
            password=make_password(password),
        )

        enseignant = Enseignant.objects.create(
            user=user,
            taux_horaire=taux_horaire,
        )
        if matieres_ids:
            enseignant.matieres.set(matieres_ids)

        messages.success(
            request,
            f"L'enseignant {user.get_full_name()} a été créé avec succès. "
            f"Mot de passe généré : <strong>{password}</strong> "
            f"(Identifiant : {username})"
        )
        return redirect('enseignants_comite:liste_comite')

    context = {
        'matieres': matieres,
    }
    return render(request, 'comite/enseignants/ajouter.html', context)
