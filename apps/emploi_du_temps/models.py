from django.db import models
from django.core.exceptions import ValidationError

CYCLE_CHOICES = [
    ('PRIMAIRE', 'Primaire'),
    ('COLLEGE', 'Collège'),
    ('LYCEE', 'Lycée'),
]

JOUR_CHOICES = [
    ('LUNDI', 'Lundi'),
    ('MARDI', 'Mardi'),
    ('MERCREDI', 'Mercredi'),
    ('JEUDI', 'Jeudi'),
    ('VENDREDI', 'Vendredi'),
]


class Matiere(models.Model):
    nom = models.CharField(max_length=100, unique=True, verbose_name='Nom de la matière')
    niveau_concerne = models.CharField(
        max_length=20,
        choices=CYCLE_CHOICES,
        verbose_name='Niveau concerné'
    )
    couleur_badge = models.CharField(
        max_length=7,
        default='#0048AE',
        verbose_name='Couleur du badge (hex)'
    )

    class Meta:
        verbose_name = 'Matière'
        verbose_name_plural = 'Matières'
        ordering = ['nom']

    def __str__(self):
        return f'{self.nom} ({self.get_niveau_concerne_display()})'


class Niveau(models.Model):
    nom = models.CharField(max_length=100, unique=True, verbose_name='Nom du niveau / classe')
    cycle = models.CharField(
        max_length=20,
        choices=CYCLE_CHOICES,
        verbose_name='Cycle'
    )
    frais_inscription = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        verbose_name='Frais d\'inscription (FCFA)'
    )

    class Meta:
        verbose_name = 'Niveau / Classe'
        verbose_name_plural = 'Niveaux / Classes'
        ordering = ['cycle', 'nom']

    def __str__(self):
        return f'{self.nom} ({self.get_cycle_display()})'


class EmploiDuTemps(models.Model):
    session = models.ForeignKey(
        'core.SessionVacances',
        on_delete=models.CASCADE,
        related_name='creneaux',
        verbose_name='Session'
    )
    jour = models.CharField(
        max_length=10,
        choices=JOUR_CHOICES,
        verbose_name='Jour'
    )
    heure_debut = models.TimeField(verbose_name='Heure de début')
    heure_fin = models.TimeField(verbose_name='Heure de fin')
    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.CASCADE,
        related_name='creneaux',
        verbose_name='Matière'
    )
    niveau = models.ForeignKey(
        Niveau,
        on_delete=models.CASCADE,
        related_name='creneaux',
        verbose_name='Niveau / Classe'
    )
    enseignant = models.ForeignKey(
        'enseignants.Enseignant',
        on_delete=models.CASCADE,
        related_name='creneaux',
        verbose_name='Enseignant'
    )
    salle = models.CharField(max_length=50, blank=True, verbose_name='Salle')

    class Meta:
        verbose_name = 'Créneau d\'emploi du temps'
        verbose_name_plural = 'Créneaux d\'emploi du temps'
        ordering = ['session', 'jour', 'heure_debut']
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'jour', 'heure_debut', 'enseignant'],
                name='unique_enseignant_creneau_simultane'
            ),
        ]

    def __str__(self):
        return f'{self.get_jour_display()} {self.heure_debut}-{self.heure_fin} : {self.matiere} ({self.niveau})'

    def clean(self):
        super().clean()
        if self.heure_fin <= self.heure_debut:
            raise ValidationError('L\'heure de fin doit être postérieure à l\'heure de début.')

        # Validate within 08:00-13:00
        from datetime import time
        if self.heure_debut < time(8, 0) or self.heure_fin > time(13, 0):
            raise ValidationError('Les créneaux doivent être compris entre 08:00 et 13:00.')

        # Check for overlapping slots for the same teacher
        if self.enseignant_id and self.jour and self.heure_debut and self.heure_fin:
            overlapping = EmploiDuTemps.objects.filter(
                enseignant=self.enseignant,
                jour=self.jour,
                session=self.session,
                heure_debut__lt=self.heure_fin,
                heure_fin__gt=self.heure_debut,
            ).exclude(pk=self.pk)
            if overlapping.exists():
                raise ValidationError(
                    f'Cet enseignant a déjà un créneau qui chevauche cette plage horaire : {overlapping.first()}'
                )
