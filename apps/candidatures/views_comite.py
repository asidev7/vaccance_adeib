from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from apps.accounts.decorators import staff_comite_required
from apps.candidatures.models import CandidatureEnseignant
from apps.accounts.models import CustomUser
from apps.enseignants.models import Enseignant
import random
import string


def _generate_username(nom_complet):
    """Generate a unique username from full name."""
    base = nom_complet.lower().replace(' ', '').replace("'", "").replace('-', '')
    # Remove non-ascii chars
    import unicodedata
    base = ''.join(c for c in unicodedata.normalize('NFKD', base) if not unicodedata.combining(c))
    base = ''.join(c for c in base if c.isalnum())

    suffix = ''.join(random.choices(string.digits, k=3))
    username = f'{base}{suffix}'

    # Ensure uniqueness
    while CustomUser.objects.filter(username=username).exists():
        suffix = ''.join(random.choices(string.digits, k=4))
        username = f'{base}{suffix}'

    return username


def _generate_password(length=10):
    """Generate a random temporary password."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


@login_required
@staff_comite_required
def liste(request):
    statut_filter = request.GET.get('statut', '').strip()
    candidatures = CandidatureEnseignant.objects.all()

    if statut_filter:
        candidatures = candidatures.filter(statut=statut_filter)

    candidatures = candidatures.order_by('-date_soumission')

    context = {
        'candidatures': candidatures,
        'statut_filter': statut_filter,
    }
    return render(request, 'comite/candidatures/list.html', context)


@login_required
@staff_comite_required
def detail(request, id):
    candidature = get_object_or_404(CandidatureEnseignant.objects.prefetch_related('matieres_souhaitees'), pk=id)

    context = {
        'candidature': candidature,
    }
    return render(request, 'comite/candidatures/detail.html', context)


@login_required
@staff_comite_required
def accepter(request, id):
    candidature = get_object_or_404(CandidatureEnseignant, pk=id)

    if candidature.statut != 'EN_ATTENTE':
        messages.warning(request, f'Cette candidature a déjà été traitée (statut: {candidature.get_statut_display()}).')
        return redirect('candidatures_comite:liste_comite')

    if request.method == 'POST':
        # Generate credentials
        username = _generate_username(candidature.nom_complet)
        password = _generate_password()

        # Create user account
        user = CustomUser.objects.create_user(
            username=username,
            password=password,
            email=candidature.email,
            role='enseignant',
            first_name=candidature.nom_complet.split()[0] if candidature.nom_complet.split() else '',
            last_name=' '.join(candidature.nom_complet.split()[1:]) if len(candidature.nom_complet.split()) > 1 else '',
            telephone=candidature.telephone,
        )

        # Create enseignant
        enseignant = Enseignant.objects.create(
            user=user,
            candidature_origine=candidature,
        )
        # Copy matieres from candidature
        enseignant.matieres.set(candidature.matieres_souhaitees.all())

        # Update candidature
        candidature.statut = 'ACCEPTE'
        candidature.traite_par = request.user
        candidature.date_traitement = timezone.now()
        candidature.save()

        messages.success(
            request,
            f'Candidature acceptée ! '
            f'Identifiant : {username} | '
            f'Mot de passe temporaire : {password}'
        )
        return redirect('candidatures_comite:liste_comite')

    # GET request — confirmation page
    context = {
        'candidature': candidature,
    }
    return render(request, 'comite/candidatures/detail.html', context)


@login_required
@staff_comite_required
def refuser(request, id):
    candidature = get_object_or_404(CandidatureEnseignant, pk=id)

    if candidature.statut != 'EN_ATTENTE':
        messages.warning(request, f'Cette candidature a déjà été traitée (statut: {candidature.get_statut_display()}).')
        return redirect('candidatures_comite:liste_comite')

    candidature.statut = 'REFUSE'
    candidature.traite_par = request.user
    candidature.date_traitement = timezone.now()
    candidature.save()

    messages.warning(request, f'Candidature de {candidature.nom_complet} refusée.')
    return redirect('candidatures_comite:liste_comite')
