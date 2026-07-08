from django.db import models
from django.core.exceptions import ValidationError


class SessionVacances(models.Model):
    nom = models.CharField(max_length=200, verbose_name='Nom de la session')
    date_debut = models.DateField(verbose_name='Date de début')
    date_fin = models.DateField(verbose_name='Date de fin')
    annee = models.PositiveIntegerField(verbose_name='Année')
    est_active = models.BooleanField(default=False, verbose_name='Session active')
    frais_inscription = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        verbose_name='Frais d\'inscription (FCFA)'
    )
    tolerance_retard_minutes = models.PositiveIntegerField(
        default=10,
        verbose_name='Tolérance de retard (minutes)'
    )

    class Meta:
        verbose_name = 'Session de vacances'
        verbose_name_plural = 'Sessions de vacances'
        ordering = ['-date_debut']

    def __str__(self):
        return f'{self.nom} ({self.annee})'

    def clean(self):
        super().clean()
        if self.date_fin < self.date_debut:
            raise ValidationError('La date de fin doit être postérieure à la date de début.')
        # Ensure only one active session
        if self.est_active:
            existing = SessionVacances.objects.filter(est_active=True).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(
                    f'La session "{existing.first().nom}" est déjà active. '
                    'Désactivez-la avant d\'en activer une autre.'
                )
