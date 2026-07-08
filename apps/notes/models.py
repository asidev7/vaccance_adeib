from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg, Sum
from decimal import Decimal


class CoefficientMatiere(models.Model):
    """Coefficient d'une matière pour un niveau/classe spécifique."""
    matiere = models.ForeignKey(
        'emploi_du_temps.Matiere',
        on_delete=models.CASCADE,
        related_name='coefficients',
        verbose_name='Matière'
    )
    niveau = models.ForeignKey(
        'emploi_du_temps.Niveau',
        on_delete=models.CASCADE,
        related_name='coefficients',
        verbose_name='Niveau / Classe'
    )
    coefficient = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=1.0,
        validators=[MinValueValidator(Decimal('0.5')), MaxValueValidator(Decimal('10.0'))],
        verbose_name='Coefficient'
    )

    class Meta:
        verbose_name = 'Coefficient matière'
        verbose_name_plural = 'Coefficients matières'
        unique_together = ['matiere', 'niveau']

    def __str__(self):
        return f'{self.matiere.nom} ({self.niveau.nom}) — Coef: {self.coefficient}'


class Note(models.Model):
    """Note attribuée à un élève par un enseignant pour une matière."""
    inscription = models.ForeignKey(
        'inscriptions.Inscription',
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name='Élève'
    )
    matiere = models.ForeignKey(
        'emploi_du_temps.Matiere',
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name='Matière'
    )
    enseignant = models.ForeignKey(
        'enseignants.Enseignant',
        on_delete=models.CASCADE,
        related_name='notes_saisies',
        verbose_name='Enseignant'
    )
    session = models.ForeignKey(
        'core.SessionVacances',
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name='Session'
    )
    note = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('20.0'))],
        verbose_name='Note /20'
    )
    observation = models.TextField(
        blank=True,
        verbose_name='Observation'
    )
    date_ajout = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date d\'ajout'
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name='Dernière modification'
    )

    class Meta:
        verbose_name = 'Note'
        verbose_name_plural = 'Notes'
        unique_together = ['inscription', 'matiere', 'session']
        ordering = ['matiere__nom']

    def __str__(self):
        return f'{self.inscription.nom_eleve} {self.inscription.prenom_eleve} — {self.matiere.nom}: {self.note}/20'

    @property
    def coefficient(self):
        """Récupère le coefficient de la matière pour le niveau de l'élève."""
        try:
            coeff = CoefficientMatiere.objects.get(
                matiere=self.matiere,
                niveau=self.inscription.niveau
            )
            return coeff.coefficient
        except CoefficientMatiere.DoesNotExist:
            return Decimal('1.0')

    @property
    def note_ponderee(self):
        """Note multipliée par le coefficient."""
        return self.note * self.coefficient


class BulletinConfig(models.Model):
    """Configuration de la génération des bulletins par niveau et session."""
    niveau = models.ForeignKey(
        'emploi_du_temps.Niveau',
        on_delete=models.CASCADE,
        related_name='bulletins_config',
        verbose_name='Niveau / Classe'
    )
    session = models.ForeignKey(
        'core.SessionVacances',
        on_delete=models.CASCADE,
        related_name='bulletins_config',
        verbose_name='Session'
    )
    saisie_ouverte = models.BooleanField(
        default=False,
        verbose_name='Saisie des notes ouverte'
    )
    bulletin_generable = models.BooleanField(
        default=False,
        verbose_name='Bulletins générables'
    )

    class Meta:
        verbose_name = 'Configuration bulletin'
        verbose_name_plural = 'Configurations bulletins'
        unique_together = ['niveau', 'session']

    def __str__(self):
        return f'{self.niveau.nom} — {self.session.nom}: {"Saisie ouverte" if self.saisie_ouverte else "Saisie fermée"}'


class BulletinGenere(models.Model):
    """Bulletin PDF généré pour un élève."""
    inscription = models.ForeignKey(
        'inscriptions.Inscription',
        on_delete=models.CASCADE,
        related_name='bulletins_generes',
        verbose_name='Élève'
    )
    session = models.ForeignKey(
        'core.SessionVacances',
        on_delete=models.CASCADE,
        related_name='bulletins_generes',
        verbose_name='Session'
    )
    fichier_pdf = models.FileField(
        upload_to='bulletins/%Y/%m/',
        verbose_name='Fichier PDF'
    )
    genere_le = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Généré le'
    )
    genere_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bulletins_generes',
        verbose_name='Généré par'
    )

    class Meta:
        verbose_name = 'Bulletin généré'
        verbose_name_plural = 'Bulletins générés'
        ordering = ['-genere_le']

    def __str__(self):
        return f'Bulletin {self.inscription.nom_eleve} {self.inscription.prenom_eleve} — {self.session.nom}'
