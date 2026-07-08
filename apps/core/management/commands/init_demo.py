"""
Management command to populate demo data for the ADEIB platform v2.

Creates:
- 3 Comité staff accounts (admin, tresorier, secretaire)
- Active vacation session
- Matières, Niveaux with per-niveau fees
- Teacher candidatures, users, and Enseignants with QR codes
- Sample timetable creneaux
- Sample inscriptions
"""
from datetime import time, date
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import CustomUser
from apps.core.models import SessionVacances
from apps.emploi_du_temps.models import Matiere, Niveau, EmploiDuTemps
from apps.enseignants.models import Enseignant
from apps.candidatures.models import CandidatureEnseignant
from apps.inscriptions.models import Inscription


# Per-niveau fees: CM1-CM2=1000, 6e-5e=1500, 4e-3e=2000, 2nde-1ere-Tle=3500
NIVEAU_FRAIS = {
    'CM1': 1000, 'CM2': 1000,
    '6e': 1500, '5e': 1500,
    '4e': 2000, '3e': 2000,
    '2nde': 3500, '1ère': 3500, 'Tle': 3500,
}


class Command(BaseCommand):
    help = 'Initialise la base de données avec des données de démonstration.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=== Initialisation des données v2 ==='))
        self.stdout.write('')

        # ---- 1. Comité staff accounts ----
        self.stdout.write('Création des comptes comité...')
        comite_accounts = [
            {'username': 'admin', 'email': 'admin@adeib.site', 'role': 'admin',
             'first_name': 'Admin', 'last_name': 'ADEIB', 'password': 'admin123',
             'is_superuser': True, 'is_staff': True},
            {'username': 'tresorier', 'email': 'tresorier@adeib.site', 'role': 'tresorier',
             'first_name': 'Trésorier', 'last_name': 'ADEIB', 'password': 'tresorier123'},
            {'username': 'secretaire', 'email': 'secretaire@adeib.site', 'role': 'secretaire',
             'first_name': 'Secrétaire', 'last_name': 'ADEIB', 'password': 'secretaire123'},
        ]
        for acc in comite_accounts:
            user, created = CustomUser.objects.get_or_create(
                username=acc['username'],
                defaults={k: v for k, v in acc.items() if k not in ('username', 'password')},
            )
            if created:
                user.set_password(acc['password'])
                user.save()
                self.stdout.write(f'  ✅ {acc["username"]} / {acc["password"]} ({acc["role"]})')
            else:
                self.stdout.write(f'  ℹ️  {acc["username"]} existe déjà')

        # ---- 2. Active session ----
        self.stdout.write('Création de la session active...')
        session, _ = SessionVacances.objects.get_or_create(
            nom='Vacances Août 2026',
            defaults={
                'date_debut': date(2026, 8, 1),
                'date_fin': date(2026, 8, 31),
                'annee': 2026,
                'est_active': True,
                'frais_inscription': 0,  # Deprecated: per-niveau fees now
                'tolerance_retard_minutes': 10,
            },
        )
        if not session.est_active:
            SessionVacances.objects.filter(est_active=True).update(est_active=False)
            session.est_active = True
            session.save()
        self.stdout.write(f'  ✅ Session : {session.nom}')

        # ---- 3. Matières ----
        self.stdout.write('Création des matières...')
        matieres_data = [
            ('Maths', 'COLLEGE', '#E74C3C'),
            ('Français', 'PRIMAIRE', '#3498DB'),
            ('Anglais', 'LYCEE', '#2ECC71'),
            ('PC', 'COLLEGE', '#F39C12'),
            ('SVT', 'COLLEGE', '#9B59B6'),
        ]
        matieres_list = []
        for nom, niveau, couleur in matieres_data:
            m, _ = Matiere.objects.get_or_create(
                nom=nom, defaults={'niveau_concerne': niveau, 'couleur_badge': couleur}
            )
            matieres_list.append(m)
        self.stdout.write(f'  ✅ {len(matieres_list)} matières')

        # ---- 4. Niveaux with per-niveau fees ----
        self.stdout.write('Création des niveaux avec frais...')
        niveaux_data = [
            ('CM1', 'PRIMAIRE'), ('CM2', 'PRIMAIRE'),
            ('6e', 'COLLEGE'), ('5e', 'COLLEGE'),
            ('4e', 'COLLEGE'), ('3e', 'COLLEGE'),
            ('2nde', 'LYCEE'), ('1ère', 'LYCEE'), ('Tle', 'LYCEE'),
        ]
        niveaux_dict = {}
        for nom, cycle in niveaux_data:
            n, created = Niveau.objects.get_or_create(
                nom=nom,
                defaults={'cycle': cycle, 'frais_inscription': NIVEAU_FRAIS.get(nom, 0)},
            )
            if not created and n.frais_inscription == 0:
                n.frais_inscription = NIVEAU_FRAIS.get(nom, 0)
                n.save(update_fields=['frais_inscription'])
            niveaux_dict[nom] = n
            self.stdout.write(f'  {"✅" if created else "ℹ️"} {n.nom} — {n.frais_inscription} FCFA')

        # ---- 5. Teachers ----
        self.stdout.write('Création des enseignants...')
        teachers_data = [
            {'username': 'teacher1', 'first_name': 'Kouassi', 'last_name': 'Koffi',
             'password': 'teacher123', 'telephone': '0101010101', 'taux': 1500, 'mat_idx': 0},
            {'username': 'teacher2', 'first_name': 'Aminata', 'last_name': 'Diallo',
             'password': 'teacher123', 'telephone': '0202020202', 'taux': 1200, 'mat_idx': 1},
            {'username': 'teacher3', 'first_name': 'Paul', 'last_name': 'Ahouansou',
             'password': 'teacher123', 'telephone': '0303030303', 'taux': 1000, 'mat_idx': 2},
        ]
        enseignants_list = []
        for td in teachers_data:
            cand, _ = CandidatureEnseignant.objects.get_or_create(
                email=f'{td["username"]}@email.com',
                defaults={
                    'nom_complet': f'{td["first_name"]} {td["last_name"]}',
                    'telephone': td['telephone'],
                    'date_naissance': date(1995, 5, 15),
                    'niveau_etude': 'MASTER1',
                    'motivation': 'Candidature de démonstration.',
                    'statut': 'ACCEPTE',
                    'date_traitement': timezone.now(),
                },
            )
            user, _ = CustomUser.objects.get_or_create(
                username=td['username'],
                defaults={
                    'email': f'{td["username"]}@email.com',
                    'role': 'enseignant',
                    'first_name': td['first_name'],
                    'last_name': td['last_name'],
                    'telephone': td['telephone'],
                    'est_actif': True,
                },
            )
            user.set_password(td['password'])
            user.save()
            ens, _ = Enseignant.objects.get_or_create(
                user=user,
                defaults={'candidature_origine': cand, 'taux_horaire': td['taux'], 'est_actif': True},
            )
            ens.matieres.add(matieres_list[td['mat_idx']])
            enseignants_list.append(ens)
            self.stdout.write(f'  ✅ {td["username"]} / {td["password"]} (QR: {ens.qr_code_uid})')

        # ---- 6. Emploi du temps ----
        self.stdout.write('Création des créneaux...')
        creneaux_data = [
            ('LUNDI', time(8, 0), time(10, 0), 0, '6e', 0, 'Salle A'),
            ('LUNDI', time(10, 0), time(12, 0), 1, 'CM1', 1, 'Salle B'),
            ('LUNDI', time(8, 0), time(10, 0), 2, '2nde', 2, 'Salle C'),
            ('MARDI', time(8, 0), time(10, 0), 3, '3e', 0, 'Salle A'),
            ('MARDI', time(10, 0), time(12, 0), 4, '5e', 1, 'Salle B'),
            ('MERCREDI', time(8, 0), time(10, 0), 0, '4e', 2, 'Salle C'),
            ('MERCREDI', time(10, 0), time(12, 0), 2, '1ère', 0, 'Salle A'),
        ]
        edt_count = 0
        for jour, debut, fin, mat_idx, niv_nom, ens_idx, salle in creneaux_data:
            _, created = EmploiDuTemps.objects.get_or_create(
                session=session, jour=jour, heure_debut=debut,
                enseignant=enseignants_list[ens_idx],
                defaults={
                    'heure_fin': fin, 'matiere': matieres_list[mat_idx],
                    'niveau': niveaux_dict[niv_nom], 'salle': salle,
                },
            )
            if created:
                edt_count += 1
        self.stdout.write(f'  ✅ {edt_count} créneaux')

        # ---- 7. Inscriptions with per-niveau fees ----
        self.stdout.write('Création des inscriptions...')
        inscriptions_data = [
            ('Mensah', 'Jean', '6e', 'Mensah Pierre', '0505050505', 'PAYE'),
            ('Soro', 'Marie', 'CM1', 'Soro Amadou', '0606060606', 'PARTIEL'),
            ('Bamba', 'Fatou', '2nde', 'Bamba Issa', '0707070707', 'IMPAYE'),
            ('Yao', 'Koffi', '5e', 'Yao Kouame', '0808080808', 'PAYE'),
        ]
        ins_count = 0
        for nom, prenom, niv_nom, parent, tel, statut in inscriptions_data:
            frais = NIVEAU_FRAIS.get(niv_nom, 5000)
            montant_paye = frais if statut == 'PAYE' else (frais // 2 if statut == 'PARTIEL' else 0)
            ins, created = Inscription.objects.get_or_create(
                nom_eleve=nom, prenom_eleve=prenom, date_naissance=date(2013, 1, 1),
                session=session,
                defaults={
                    'niveau': niveaux_dict[niv_nom],
                    'nom_parent': parent, 'telephone_parent': tel,
                    'montant_du': frais, 'montant_paye': montant_paye,
                    'statut_paiement': statut,
                },
            )
            if created:
                ins_count += 1
        self.stdout.write(f'  ✅ {ins_count} inscriptions')

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Données initialisées avec succès ==='))
        self.stdout.write(f'  Comité : admin/admin123 | tresorier/tresorier123 | secretaire/secretaire123')
        self.stdout.write(f'  Enseignants : teacher1, teacher2, teacher3 / teacher123')
        self.stdout.write(f'  Frais par niveau : {NIVEAU_FRAIS}')
