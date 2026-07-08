import json
from datetime import datetime, date, time, timedelta
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from apps.accounts.decorators import secretaire_required
from apps.core.models import SessionVacances
from apps.enseignants.models import Enseignant, Presence
from apps.emploi_du_temps.models import EmploiDuTemps

JOUR_MAPPING = {
    0: 'LUNDI', 1: 'MARDI', 2: 'MERCREDI', 3: 'JEUDI', 4: 'VENDREDI',
}


@login_required
@secretaire_required
def scanner(request):
    return render(request, 'comite/scanner.html')


@login_required
@secretaire_required
@csrf_exempt
def api_enregistrer_presence(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

    try:
        data = json.loads(request.body)
        qr_code_uid = data.get('qr_code_uid', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})

    if not qr_code_uid:
        return JsonResponse({'success': False, 'error': 'QR code UID manquant'})

    # Find enseignant by QR code UID
    try:
        enseignant = Enseignant.objects.select_related('user').get(qr_code_uid=qr_code_uid)
    except Enseignant.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'QR code non reconnu. Enseignant introuvable.'})

    if not enseignant.est_actif:
        return JsonResponse({'success': False, 'error': 'Cet enseignant est désactivé.'})

    # Determine current day and time
    now = timezone.localtime()
    jour_idx = now.weekday()  # 0=Monday, 6=Sunday

    if jour_idx >= 5:  # Saturday or Sunday
        return JsonResponse({'success': False, 'error': 'Pas de cours le week-end.'})

    jour = JOUR_MAPPING[jour_idx]
    heure_actuelle = now.time()

    # Get active session
    session_active = SessionVacances.objects.filter(est_active=True).first()
    if not session_active:
        return JsonResponse({'success': False, 'error': 'Aucune session active.'})

    # Find the creneau matching current time for this enseignant
    creneau = EmploiDuTemps.objects.filter(
        enseignant=enseignant,
        session=session_active,
        jour=jour,
        heure_debut__lte=heure_actuelle,
        heure_fin__gte=heure_actuelle,
    ).first()

    if not creneau:
        # Check if there's an upcoming creneau within the next 30 minutes (too early)
        creneau_proche = EmploiDuTemps.objects.filter(
            enseignant=enseignant,
            session=session_active,
            jour=jour,
            heure_debut__gt=heure_actuelle,
            heure_debut__lte=(datetime.combine(date.today(), heure_actuelle) + timedelta(minutes=30)).time(),
        ).first()
        if creneau_proche:
            return JsonResponse({
                'success': False,
                'error': f'Créneau pas encore commencé. Prochain créneau : {creneau_proche.heure_debut.strftime("%Hh%M")}.',
            })
        return JsonResponse({
            'success': False,
            'error': f'Aucun créneau trouvé pour {enseignant} à cette heure ({heure_actuelle.strftime("%Hh%M")}).',
        })

    # Determine proposed status (not final — needs validation)
    tolerance = session_active.tolerance_retard_minutes
    heure_debut_dt = datetime.combine(now.date(), creneau.heure_debut)
    heure_limite = heure_debut_dt + timedelta(minutes=tolerance)
    heure_actuelle_dt = datetime.combine(now.date(), heure_actuelle)

    if heure_actuelle_dt <= heure_limite:
        proposed_statut = 'PRESENT'
    else:
        proposed_statut = 'RETARD'

    # Create presence with EN_ATTENTE — must be validated via api_valider_presence
    presence, created = Presence.objects.get_or_create(
        enseignant=enseignant,
        creneau=creneau,
        date=now.date(),
        defaults={
            'statut': 'EN_ATTENTE',
            'valide_par': request.user,
            'commentaire': f'proposed:{proposed_statut}',
        },
    )

    if not created:
        # Extract proposed status from existing record
        existing_proposed = ''
        if presence.commentaire and presence.commentaire.startswith('proposed:'):
            existing_proposed = presence.commentaire.replace('proposed:', '')
        return JsonResponse({
            'success': True,
            'message': 'Présence déjà enregistrée pour ce créneau.',
            'presence_id': presence.id,
            'enseignant': str(enseignant),
            'statut': presence.get_statut_display(),
            'creneau': f'{creneau.matiere.nom} — {creneau.heure_debut.strftime("%Hh%M")}',
            'proposed_statut': existing_proposed,
        })

    return JsonResponse({
        'success': True,
        'message': 'Présence enregistrée (en attente de validation)',
        'presence_id': presence.id,
        'enseignant': str(enseignant),
        'statut': presence.get_statut_display(),
        'creneau': f'{creneau.matiere.nom} — {creneau.heure_debut.strftime("%Hh%M")}',
        'proposed_statut': proposed_statut,
    })


@login_required
@secretaire_required
@csrf_exempt
def api_valider_presence(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

    try:
        data = json.loads(request.body)
        presence_id = data.get('presence_id')
        statut = data.get('statut', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})

    if not presence_id:
        return JsonResponse({'success': False, 'error': 'presence_id manquant'})

    if statut not in ('PRESENT', 'RETARD', 'ABSENT'):
        return JsonResponse({'success': False, 'error': 'Statut invalide. Utilisez PRESENT, RETARD ou ABSENT.'})

    try:
        presence = Presence.objects.get(id=presence_id)
    except Presence.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Présence introuvable.'})

    presence.statut = statut
    presence.valide_par = request.user
    presence.save(update_fields=['statut', 'valide_par'])

    return JsonResponse({
        'success': True,
        'message': f'Présence validée : {presence.get_statut_display()}',
        'presence_id': presence.id,
        'enseignant': str(presence.enseignant),
        'statut': presence.get_statut_display(),
    })
