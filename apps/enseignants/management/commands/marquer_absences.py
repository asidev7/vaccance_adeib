"""
Management command to automatically mark absent teachers.

For the active session, looks at today's timetable slots where
the end time has already passed and marks teachers as absent if
no presence record exists for that (teacher, creneau, date) combination.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import SessionVacances
from apps.emploi_du_temps.models import JOUR_CHOICES, EmploiDuTemps
from apps.enseignants.models import Presence


class Command(BaseCommand):
    help = (
        'Marque automatiquement comme absents les enseignants dont le créneau '
        'est passé sans avoir été scanné.'
    )

    def handle(self, *args, **options):
        # Get the active session
        session = SessionVacances.objects.filter(est_active=True).first()
        if not session:
            self.stdout.write(self.style.WARNING(
                'Aucune session active trouvée. Aucune absence à marquer.'
            ))
            return

        # Today's date and current time
        now = timezone.now()
        aujourdhui = now.date()
        heure_actuelle = now.time()

        # Map Python weekday (0=Monday) to JOUR_CHOICES
        # JOUR_CHOICES: LUNDI, MARDI, MERCREDI, JEUDI, VENDREDI
        jour_mapping = {
            0: 'LUNDI',
            1: 'MARDI',
            2: 'MERCREDI',
            3: 'JEUDI',
            4: 'VENDREDI',
        }

        jour_code = jour_mapping.get(aujourdhui.weekday())

        if not jour_code:
            self.stdout.write(self.style.WARNING(
                f"Aujourd'hui ({aujourdhui}) est un week-end. Aucune absence à marquer."
            ))
            return

        self.stdout.write(f"Session active : {session.nom}")
        self.stdout.write(f"Date : {aujourdhui} ({jour_code})")
        self.stdout.write(f"Heure actuelle : {heure_actuelle.strftime('%H:%M')}")

        # Find all creneaux for today where heure_fin < current time
        creneaux_passes = EmploiDuTemps.objects.filter(
            session=session,
            jour=jour_code,
            heure_fin__lt=heure_actuelle,
        ).select_related('enseignant', 'matiere', 'niveau')

        absences_crees = 0
        deja_presents = 0

        for creneau in creneaux_passes:
            enseignant = creneau.enseignant

            # Check if a Presence already exists for this (enseignant, creneau, date)
            presence_existe = Presence.objects.filter(
                enseignant=enseignant,
                creneau=creneau,
                date=aujourdhui,
            ).exists()

            if presence_existe:
                deja_presents += 1
                self.stdout.write(
                    f"  [OK] {enseignant} — {creneau} : présence déjà enregistrée."
                )
            else:
                # Create absence record
                Presence.objects.create(
                    enseignant=enseignant,
                    creneau=creneau,
                    date=aujourdhui,
                    statut='ABSENT',
                    commentaire='Absence automatique',
                )
                absences_crees += 1
                self.stdout.write(
                    f"  [ABS] {enseignant} — {creneau} : marqué absent."
                )

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Résumé : {absences_crees} absence(s) créée(s), '
            f'{deja_presents} créneau(x) déjà couvert(s), '
            f'{creneaux_passes.count()} créneau(x) passé(s) au total.'
        ))
