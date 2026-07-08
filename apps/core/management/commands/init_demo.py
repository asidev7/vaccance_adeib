"""
Management command to populate demo data for the ADEIB platform.

Creates:
- 3 Comité staff accounts (admin, tresorier, secretaire)
- Active vacation session
- Matières, Niveaux with per-niveau fees
- Teacher candidatures, users, and Enseignants with QR codes
- Sample timetable creneaux
- Sample inscriptions with paiements
- Coefficients matières for each niveau
- Notes for all students
- Bulletin configurations (saisie ouverte)
"""
from datetime import time, date, datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import CustomUser
from apps.core.models import SessionVacances
from apps.emploi_du_temps.models import Matiere, Niveau, EmploiDuTemps
from apps.enseignants.models import Enseignant
from apps.candidatures.models import CandidatureEnseignant
from apps.inscriptions.models import Inscription, Paiement
from apps.notes.models import Note, CoefficientMatiere, BulletinConfig, BulletinGenere

NIVEAU_FRAIS = {
    'CM1': 25000, 'CM2': 25000,
    '6e': 30000, '5e': 30000,
    '4e': 35000, '3e': 35000,
    '2nde': 45000, '1ère': 45000, 'Tle': 50000,
}


class Command(BaseCommand):
    help = 'Initialise la base de données avec des données de démonstration complètes (notes, bulletins, etc.).'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=== 🌱 Initialisation complète des données de démo ==='))
        self.stdout.write('')

        # ── 1. Comptes staff comité ──
        self._create_comite_accounts()

        # ── 2. Session active ──
        session = self._create_session()

        # ── 3. Matières ──
        matieres = self._create_matieres()

        # ── 4. Niveaux ──
        niveaux = self._create_niveaux()

        # ── 5. Enseignants ──
        enseignants = self._create_enseignants(matieres)

        # ── 6. Emploi du temps ──
        self._create_creneaux(session, matieres, niveaux, enseignants)

        # ── 7. Inscriptions ──
        eleves_data = self._create_inscriptions(session, niveaux)

        # ── 8. Coefficients matières ──
        self._create_coefficients(matieres, niveaux)

        # ── 9. Notes des élèves ──
        self._create_notes(session, matieres, niveaux, enseignants, eleves_data)

        # ── 10. Config bulletins (saisie ouverte) ──
        self._create_bulletin_config(session, niveaux)

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== ✅ Données de démonstration créées avec succès ==='))
        self.stdout.write('')
        self.stdout.write('  📋 Comités :')
        self.stdout.write('     admin / admin123 (superuser)')
        self.stdout.write('     tresorier / tresorier123')
        self.stdout.write('     secretaire / secretaire123')
        self.stdout.write('')
        self.stdout.write('  👨‍🏫 Enseignants :')
        self.stdout.write('     teacher1 / teacher123 (Maths)')
        self.stdout.write('     teacher2 / teacher123 (Français)')
        self.stdout.write('     teacher3 / teacher123 (Anglais)')
        self.stdout.write('     teacher4 / teacher123 (PC)')
        self.stdout.write('     teacher5 / teacher123 (SVT)')
        self.stdout.write('')
        self.stdout.write('  👨‍🎓 Élèves : 8 inscrits avec notes')
        self.stdout.write('  📄 Coefficients configurés par matière/niveau')
        self.stdout.write('  ✅ Saisie des notes OUVERTE pour toutes les classes')
        self.stdout.write('')

    # ═══════════════════════════════════════════
    #  Création des comptes comité
    # ═══════════════════════════════════════════
    def _create_comite_accounts(self):
        self.stdout.write('1️⃣ Création des comptes comité...')
        comite = [
            {'username': 'admin', 'email': 'admin@adeib.site', 'role': 'admin',
             'first_name': 'Admin', 'last_name': 'ADEIB', 'password': 'admin123',
             'is_superuser': True, 'is_staff': True},
            {'username': 'tresorier', 'email': 'tresorier@adeib.site', 'role': 'tresorier',
             'first_name': 'Trésorier', 'last_name': 'ADEIB', 'password': 'tresorier123'},
            {'username': 'secretaire', 'email': 'secretaire@adeib.site', 'role': 'secretaire',
             'first_name': 'Secrétaire', 'last_name': 'ADEIB', 'password': 'secretaire123'},
        ]
        for acc in comite:
            user, created = CustomUser.objects.get_or_create(
                username=acc['username'],
                defaults={k: v for k, v in acc.items() if k != 'password'},
            )
            if created:
                user.set_password(acc['password'])
                user.save()
                self.stdout.write(f'  ✅ {acc["username"]} / {acc["password"]}')
            else:
                self.stdout.write(f'  ℹ️  {acc["username"]} existe déjà')

    # ═══════════════════════════════════════════
    #  Session vacances active
    # ═══════════════════════════════════════════
    def _create_session(self):
        self.stdout.write('2️⃣ Création de la session active...')
        session, _ = SessionVacances.objects.get_or_create(
            nom='Vacances Août 2026',
            defaults={
                'date_debut': date(2026, 8, 1),
                'date_fin': date(2026, 8, 31),
                'annee': 2026,
                'est_active': True,
                'frais_inscription': 0,
                'tolerance_retard_minutes': 10,
            },
        )
        if not session.est_active:
            SessionVacances.objects.filter(est_active=True).update(est_active=False)
            session.est_active = True
            session.save()
        self.stdout.write(f'  ✅ {session.nom} ({session.annee}) — active')
        return session

    # ═══════════════════════════════════════════
    #  Matières (détaillées)
    # ═══════════════════════════════════════════
    def _create_matieres(self):
        self.stdout.write('3️⃣ Création des matières...')
        matieres_data = [
            ('Mathématiques', 'COLLEGE', '#E74C3C'),
            ('Français', 'COLLEGE', '#3498DB'),
            ('Anglais', 'LYCEE', '#2ECC71'),
            ('Physique-Chimie', 'LYCEE', '#F39C12'),
            ('SVT', 'COLLEGE', '#9B59B6'),
            ('Histoire-Géo', 'COLLEGE', '#1ABC9C'),
            ('Lecture', 'PRIMAIRE', '#E67E22'),
            ('Calcul', 'PRIMAIRE', '#2ECC71'),
        ]
        matieres = []
        for nom, niveau, couleur in matieres_data:
            m, created = Matiere.objects.get_or_create(
                nom=nom, defaults={'niveau_concerne': niveau, 'couleur_badge': couleur}
            )
            if not created:
                m.niveau_concerne = niveau
                m.couleur_badge = couleur
                m.save()
            matieres.append(m)
            self.stdout.write(f'  {"✅" if created else "ℹ️"} {m.nom} ({m.get_niveau_concerne_display()})')
        return matieres

    # ═══════════════════════════════════════════
    #  Niveaux / Classes
    # ═══════════════════════════════════════════
    def _create_niveaux(self):
        self.stdout.write('4️⃣ Création des niveaux...')
        niveaux_data = [
            ('CM1', 'PRIMAIRE'), ('CM2', 'PRIMAIRE'),
            ('6e', 'COLLEGE'), ('5e', 'COLLEGE'),
            ('4e', 'COLLEGE'), ('3e', 'COLLEGE'),
            ('2nde A', 'LYCEE'), ('1ère D', 'LYCEE'), ('Tle C', 'LYCEE'),
        ]
        niveaux = {}
        for nom, cycle in niveaux_data:
            n, created = Niveau.objects.get_or_create(
                nom=nom,
                defaults={'cycle': cycle, 'frais_inscription': NIVEAU_FRAIS.get(nom, 30000)},
            )
            if not created and n.frais_inscription == 0:
                n.frais_inscription = NIVEAU_FRAIS.get(nom, 30000)
                n.save()
            niveaux[nom] = n
            self.stdout.write(f'  {"✅" if created else "ℹ️"} {n.nom} ({n.get_cycle_display()}) — {n.frais_inscription} FCFA')
        return niveaux

    # ═══════════════════════════════════════════
    #  Enseignants (5)
    # ═══════════════════════════════════════════
    def _create_enseignants(self, matieres):
        self.stdout.write('5️⃣ Création des enseignants...')
        teachers = [
            ('teacher1', 'Kouassi', 'Koffi', '0101010101', 1500, 0),      # Maths
            ('teacher2', 'Aminata', 'Diallo', '0202020202', 1200, 1),      # Français
            ('teacher3', 'Emmanuella', 'Lawson', '0303030303', 1300, 2),   # Anglais
            ('teacher4', 'Richard', 'Houénou', '0404040404', 1400, 3),     # PC
            ('teacher5', 'Fidèle', 'Tossou', '0505050505', 1100, 4),       # SVT
        ]
        enseignants = []
        for username, first, last, tel, taux, mat_idx in teachers:
            cand, _ = CandidatureEnseignant.objects.get_or_create(
                email=f'{username}@email.com',
                defaults={
                    'nom_complet': f'{first} {last}',
                    'telephone': tel,
                    'date_naissance': date(1992, 3, 15),
                    'niveau_etude': 'MASTER2',
                    'motivation': f'Enseignant de {matieres[mat_idx].nom} expérimenté.',
                    'statut': 'ACCEPTE',
                    'date_traitement': timezone.now(),
                },
            )
            user, _ = CustomUser.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@email.com',
                    'role': 'enseignant',
                    'first_name': first,
                    'last_name': last,
                    'telephone': tel,
                    'est_actif': True,
                },
            )
            user.set_password('teacher123')
            user.save()
            ens, _ = Enseignant.objects.get_or_create(
                user=user,
                defaults={'candidature_origine': cand, 'taux_horaire': taux, 'est_actif': True},
            )
            ens.matieres.add(matieres[mat_idx])
            if mat_idx == 0:  # Maths → aussi Calcul
                ens.matieres.add(matieres[7])
            elif mat_idx == 1:  # Français → aussi Lecture, HG
                ens.matieres.add(matieres[6])
            enseignants.append(ens)
            self.stdout.write(f'  ✅ {username} / teacher123 — {matieres[mat_idx].nom}')
        return enseignants

    # ═══════════════════════════════════════════
    #  Emploi du temps
    # ═══════════════════════════════════════════
    def _create_creneaux(self, session, matieres, niveaux, enseignants):
        self.stdout.write('6️⃣ Création de l\'emploi du temps...')
        # (jour, debut, fin, matiere_idx, niveau_nom, enseignant_idx, salle)
        creneaux = [
            ('LUNDI', time(8, 0), time(10, 0), 0, '6e', 0, 'Salle 1'),
            ('LUNDI', time(10, 0), time(12, 0), 1, 'CM1', 1, 'Salle 2'),
            ('LUNDI', time(8, 0), time(10, 0), 2, '2nde A', 2, 'Salle 3'),
            ('LUNDI', time(10, 0), time(12, 0), 3, '1ère D', 3, 'Salle 4'),
            ('MARDI', time(8, 0), time(10, 0), 3, 'Tle C', 3, 'Salle 4'),
            ('MARDI', time(10, 0), time(12, 0), 4, '5e', 4, 'Salle 2'),
            ('MARDI', time(8, 0), time(10, 0), 0, '4e', 0, 'Salle 1'),
            ('MERCREDI', time(8, 0), time(10, 0), 1, '3e', 1, 'Salle 3'),
            ('MERCREDI', time(10, 0), time(12, 0), 2, '2nde A', 2, 'Salle 3'),
            ('MERCREDI', time(8, 0), time(10, 0), 0, 'Tle C', 0, 'Salle 1'),
            ('JEUDI', time(8, 0), time(10, 0), 4, '6e', 4, 'Salle 2'),
            ('JEUDI', time(10, 0), time(12, 0), 1, '5e', 1, 'Salle 3'),
            ('VENDREDI', time(8, 0), time(10, 0), 2, '4e', 2, 'Salle 1'),
            ('VENDREDI', time(10, 0), time(12, 0), 0, '3e', 0, 'Salle 4'),
        ]
        count = 0
        for jour, debut, fin, mat_idx, niv_nom, ens_idx, salle in creneaux:
            obj, created = EmploiDuTemps.objects.get_or_create(
                session=session, jour=jour, heure_debut=debut,
                enseignant=enseignants[ens_idx],
                defaults={
                    'heure_fin': fin, 'matiere': matieres[mat_idx],
                    'niveau': niveaux[niv_nom], 'salle': salle,
                },
            )
            if created:
                count += 1
        self.stdout.write(f'  ✅ {count} créneaux créés')

    # ═══════════════════════════════════════════
    #  Inscriptions (8 élèves)
    # ═══════════════════════════════════════════
    def _create_inscriptions(self, session, niveaux):
        self.stdout.write('7️⃣ Création des inscriptions avec paiements...')
        eleves = [
            ('Mensah', 'Jean', '2008-03-15', '6e', 'Mensah Pierre', '91000001', 'PAYE', 30000),
            ('Soro', 'Marie', '2011-06-22', 'CM1', 'Soro Amadou', '91000002', 'PAYE', 25000),
            ('Bamba', 'Fatou', '2006-09-10', '2nde A', 'Bamba Issa', '91000003', 'PARTIEL', 45000),
            ('Yao', 'Koffi', '2009-01-05', '5e', 'Yao Kouame', '91000004', 'PAYE', 30000),
            ('Akakpo', 'Estelle', '2010-12-18', 'CM2', 'Akakpo David', '91000005', 'PAYE', 25000),
            ('Hounkpatin', 'Junior', '2007-07-30', '3e', 'Hounkpatin Paul', '91000006', 'IMPAYE', 35000),
            ('Dossa', 'Gloria', '2005-04-25', '1ère D', 'Dossa Michel', '91000007', 'PAYE', 45000),
            ('Adanle', 'Isaac', '2004-11-02', 'Tle C', 'Adanle Joseph', '91000008', 'PARTIEL', 50000),
        ]
        eleves_data = []
        from django.contrib.auth import get_user_model
        admin_user = get_user_model().objects.filter(role='admin').first()

        for nom, prenom, naiss, niv_nom, parent, tel, statut, frais in eleves:
            ins, created = Inscription.objects.get_or_create(
                nom_eleve=nom, prenom_eleve=prenom, date_naissance=date.fromisoformat(naiss),
                session=session, niveau=niveaux[niv_nom],
                defaults={
                    'nom_parent': parent, 'telephone_parent': tel,
                    'montant_du': frais,
                    'montant_paye': frais if statut == 'PAYE' else (frais // 2 if statut == 'PARTIEL' else 0),
                    'statut_paiement': statut,
                },
            )
            if created:
                # Créer un paiement si payé ou partiel
                if statut in ('PAYE', 'PARTIEL'):
                    montant = frais if statut == 'PAYE' else frais // 2
                    Paiement.objects.create(
                        inscription=ins,
                        montant=montant,
                        methode='ESPECES',
                        enregistre_par=admin_user,
                        statut='CONFIRME',
                        date_paiement=timezone.now() - timezone.timedelta(days=1),
                    )
            eleves_data.append((ins, niv_nom))
            self.stdout.write(f'  {"✅" if created else "ℹ️"} {nom} {prenom} — {niv_nom} ({statut})')
        return eleves_data

    # ═══════════════════════════════════════════
    #  Coefficients matières
    # ═══════════════════════════════════════════
    def _create_coefficients(self, matieres, niveaux):
        self.stdout.write('8️⃣ Création des coefficients...')
        # (matiere_nom, niveau_nom, coefficient)
        coeffs = [
            # Primaire
            ('Mathématiques', 'CM1', 3.0), ('Français', 'CM1', 3.0),
            ('Lecture', 'CM1', 2.0), ('Calcul', 'CM1', 2.0),
            ('Mathématiques', 'CM2', 3.0), ('Français', 'CM2', 3.0),
            ('Lecture', 'CM2', 2.0), ('Calcul', 'CM2', 2.0),
            # Collège
            ('Mathématiques', '6e', 4.0), ('Français', '6e', 3.0),
            ('Anglais', '6e', 2.0), ('SVT', '6e', 2.0), ('Histoire-Géo', '6e', 2.0),
            ('Mathématiques', '5e', 4.0), ('Français', '5e', 3.0),
            ('Anglais', '5e', 2.0), ('SVT', '5e', 2.0), ('Histoire-Géo', '5e', 2.0),
            ('Mathématiques', '4e', 4.0), ('Français', '4e', 3.0),
            ('Anglais', '4e', 2.0), ('PC', '4e', 2.0), ('SVT', '4e', 2.0),
            ('Mathématiques', '3e', 4.0), ('Français', '3e', 3.0),
            ('Anglais', '3e', 2.0), ('PC', '3e', 2.0), ('SVT', '3e', 2.0),
            # Lycée
            ('Mathématiques', '2nde A', 5.0), ('Français', '2nde A', 3.0),
            ('Anglais', '2nde A', 3.0), ('PC', '2nde A', 2.0), ('SVT', '2nde A', 2.0),
            ('Mathématiques', '1ère D', 5.0), ('Français', '1ère D', 3.0),
            ('Anglais', '1ère D', 3.0), ('PC', '1ère D', 3.0), ('SVT', '1ère D', 2.0),
            ('Mathématiques', 'Tle C', 6.0), ('Français', 'Tle C', 2.0),
            ('Anglais', 'Tle C', 2.0), ('PC', 'Tle C', 4.0), ('SVT', 'Tle C', 2.0),
        ]
        count = 0
        for mat_nom, niv_nom, coef in coeffs:
            mat = next((m for m in matieres if m.nom == mat_nom), None)
            niv = niveaux.get(niv_nom)
            if mat and niv:
                _, created = CoefficientMatiere.objects.get_or_create(
                    matiere=mat, niveau=niv,
                    defaults={'coefficient': Decimal(str(coef))},
                )
                if created:
                    count += 1
        self.stdout.write(f'  ✅ {count} coefficients créés')

    # ═══════════════════════════════════════════
    #  Notes des élèves (données réalistes)
    # ═══════════════════════════════════════════
    def _create_notes(self, session, matieres, niveaux, enseignants, eleves_data):
        self.stdout.write('9️⃣ Création des notes des élèves...')
        notes_by_niveau = {
            '6e': {
                'Mathématiques': [14.0, 12.5, None, 0, 0, 0, 0, 0],
                'Français': [13.0, 11.0, None, 0, 0, 0, 0, 0],
                'Anglais': [15.0, 10.5, None, 0, 0, 0, 0, 0],
                'SVT': [16.0, 14.0, None, 0, 0, 0, 0, 0],
                'Histoire-Géo': [12.0, 13.5, None, 0, 0, 0, 0, 0],
            },
            'CM1': {
                'Mathématiques': [0, 11.5, 0, 0, 0, 0, 0, 0],
                'Français': [0, 10.0, 0, 0, 0, 0, 0, 0],
                'Lecture': [0, 14.0, 0, 0, 0, 0, 0, 0],
                'Calcul': [0, 12.0, 0, 0, 0, 0, 0, 0],
            },
            'CM2': {
                'Mathématiques': [0, 0, 0, 0, 15.5, 0, 0, 0],
                'Français': [0, 0, 0, 0, 14.0, 0, 0, 0],
                'Lecture': [0, 0, 0, 0, 17.0, 0, 0, 0],
                'Calcul': [0, 0, 0, 0, 13.5, 0, 0, 0],
            },
            '5e': {
                'Mathématiques': [0, 0, 0, 8.5, 0, 0, 0, 0],
                'Français': [0, 0, 0, 9.0, 0, 0, 0, 0],
                'Anglais': [0, 0, 0, 11.0, 0, 0, 0, 0],
                'SVT': [0, 0, 0, 10.5, 0, 0, 0, 0],
                'Histoire-Géo': [0, 0, 0, 12.0, 0, 0, 0, 0],
            },
            '3e': {
                'Mathématiques': [0, 0, 0, 0, 0, 7.5, 0, 0],
                'Français': [0, 0, 0, 0, 0, 8.0, 0, 0],
                'Anglais': [0, 0, 0, 0, 0, 9.5, 0, 0],
                'PC': [0, 0, 0, 0, 0, 6.5, 0, 0],
                'SVT': [0, 0, 0, 0, 0, 10.0, 0, 0],
            },
            '2nde A': {
                'Mathématiques': [0, 0, 11.0, 0, 0, 0, 0, 0],
                'Français': [0, 0, 12.5, 0, 0, 0, 0, 0],
                'Anglais': [0, 0, 10.0, 0, 0, 0, 0, 0],
                'PC': [0, 0, 14.0, 0, 0, 0, 0, 0],
                'SVT': [0, 0, 13.0, 0, 0, 0, 0, 0],
            },
            '1ère D': {
                'Mathématiques': [0, 0, 0, 0, 0, 0, 16.5, 0],
                'Français': [0, 0, 0, 0, 0, 0, 14.0, 0],
                'Anglais': [0, 0, 0, 0, 0, 0, 15.0, 0],
                'PC': [0, 0, 0, 0, 0, 0, 17.0, 0],
                'SVT': [0, 0, 0, 0, 0, 0, 13.5, 0],
            },
            'Tle C': {
                'Mathématiques': [0, 0, 0, 0, 0, 0, 0, 14.0],
                'Français': [0, 0, 0, 0, 0, 0, 0, 10.5],
                'Anglais': [0, 0, 0, 0, 0, 0, 0, 12.0],
                'PC': [0, 0, 0, 0, 0, 0, 0, 15.5],
                'SVT': [0, 0, 0, 0, 0, 0, 0, 11.0],
            },
        }

        # Trouver les enseignants par matière
        ens_by_mat = {}
        for ens in enseignants:
            for m in ens.matieres.all():
                ens_by_mat[m.nom] = ens

        count = 0
        for idx, (inscription, niv_nom) in enumerate(eleves_data):
            niv_notes = notes_by_niveau.get(niv_nom, {})
            for mat_nom, notes_list in niv_notes.items():
                note_val = notes_list[idx] if idx < len(notes_list) else None
                if note_val is not None:
                    mat = next((m for m in matieres if m.nom == mat_nom), None)
                    ens = ens_by_mat.get(mat_nom)
                    if mat and ens:
                        _, created = Note.objects.get_or_create(
                            inscription=inscription,
                            matiere=mat,
                            session=session,
                            enseignant=ens,
                            defaults={'note': Decimal(str(note_val)), 'observation': ''},
                        )
                        if created:
                            count += 1
        self.stdout.write(f'  ✅ {count} notes créées')

    # ═══════════════════════════════════════════
    #  Configuration bulletins
    # ═══════════════════════════════════════════
    def _create_bulletin_config(self, session, niveaux):
        self.stdout.write('🔟 Configuration des bulletins (saisie ouverte)...')
        count = 0
        for niv in niveaux.values():
            _, created = BulletinConfig.objects.get_or_create(
                niveau=niv,
                session=session,
                defaults={'saisie_ouverte': True, 'bulletin_generable': False},
            )
            if created:
                count += 1
        self.stdout.write(f'  ✅ {count} configurations de bulletins créées (saisie ouverte)')
