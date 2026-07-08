from django.db import models
from django.conf import settings


class Depense(models.Model):
    CATEGORIE_CHOICES = [
        ('FOURNITURES', 'Fournitures'),
        ('LOGIQUE', 'Logistique'),
        ('COMMUNICATION', 'Communication'),
        ('RESTAURATION', 'Restauration'),
        ('AUTRE', 'Autre'),
    ]

    libelle = models.CharField(max_length=200, verbose_name='Libellé')
    categorie = models.CharField(
        max_length=20,
        choices=CATEGORIE_CHOICES,
        verbose_name='Catégorie'
    )
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        verbose_name='Montant (FCFA)'
    )
    date_depense = models.DateField(verbose_name='Date de la dépense')
    justificatif = models.FileField(
        upload_to='justificatifs_depenses/',
        blank=True,
        null=True,
        verbose_name='Justificatif'
    )
    enregistre_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='depenses_enregistrees',
        verbose_name='Enregistré par'
    )

    class Meta:
        verbose_name = 'Dépense'
        verbose_name_plural = 'Dépenses'
        ordering = ['-date_depense']

    def __str__(self):
        return f'{self.libelle} — {self.montant} FCFA'


class Salaire(models.Model):
    STATUT_CHOICES = [
        ('CALCULE', 'Calculé'),
        ('PARTIELLEMENT_PAYE', 'Partiellement payé'),
        ('PAYE', 'Payé'),
    ]

    TYPE_PERSONNEL_CHOICES = [
        ('ENSEIGNANT', 'Enseignant'),
        ('COMITE', 'Comité'),
    ]

    enseignant = models.ForeignKey(
        'enseignants.Enseignant',
        on_delete=models.CASCADE,
        related_name='salaires',
        null=True,
        blank=True,
        verbose_name='Enseignant'
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='salaires',
        verbose_name='Bénéficiaire'
    )
    type_personnel = models.CharField(
        max_length=15,
        choices=TYPE_PERSONNEL_CHOICES,
        default='ENSEIGNANT',
        verbose_name='Type de personnel'
    )
    session = models.ForeignKey(
        'core.SessionVacances',
        on_delete=models.CASCADE,
        related_name='salaires',
        verbose_name='Session'
    )
    nombre_heures_effectuees = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        default=0,
        verbose_name='Nombre d\'heures effectuées'
    )
    taux_horaire = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        verbose_name='Taux horaire (FCFA)'
    )
    montant_brut = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name='Montant brut (FCFA)'
    )
    montant_deja_verse = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name='Montant déjà versé (FCFA)'
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='CALCULE',
        verbose_name='Statut'
    )
    date_calcul = models.DateTimeField(auto_now_add=True, verbose_name='Date de calcul')
    date_versement = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Date du dernier versement'
    )

    class Meta:
        verbose_name = 'Salaire'
        verbose_name_plural = 'Salaires'
        ordering = ['-date_calcul']
        constraints = [
            models.UniqueConstraint(
                fields=['utilisateur', 'session'],
                name='unique_salaire_utilisateur_session'
            ),
        ]

    def __str__(self):
        nom = self.enseignant.user.get_full_name() if self.enseignant else self.utilisateur.get_full_name()
        return f'Salaire {nom} — {self.session} ({self.get_statut_display()})'

    @property
    def solde_restant(self):
        return self.montant_brut - self.montant_deja_verse

    def update_statut(self):
        self.montant_deja_verse = self.versements.aggregate(
            total=models.Sum('montant')
        )['total'] or 0
        if self.montant_deja_verse >= self.montant_brut and self.montant_brut > 0:
            self.statut = 'PAYE'
            self.date_versement = self.versements.latest('date_versement').date_versement
        elif self.montant_deja_verse > 0:
            self.statut = 'PARTIELLEMENT_PAYE'
        else:
            self.statut = 'CALCULE'
        self.save(update_fields=['montant_deja_verse', 'statut', 'date_versement'])


class VersementSalaire(models.Model):
    MODE_PAIEMENT_CHOICES = [
        ('ESPECES', 'Espèces'),
        ('MOBILE_MONEY', 'Mobile Money'),
        ('VIREMENT', 'Virement bancaire'),
    ]

    salaire = models.ForeignKey(
        Salaire,
        on_delete=models.CASCADE,
        related_name='versements',
        verbose_name='Salaire'
    )
    montant = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name='Montant (FCFA)'
    )
    date_versement = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date du versement'
    )
    verse_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='versements_effectues',
        verbose_name='Versé par'
    )
    mode_paiement = models.CharField(
        max_length=15,
        choices=MODE_PAIEMENT_CHOICES,
        default='ESPECES',
        verbose_name='Mode de paiement'
    )

    class Meta:
        verbose_name = 'Versement de salaire'
        verbose_name_plural = 'Versements de salaire'
        ordering = ['-date_versement']

    def __str__(self):
        return f'Versement {self.montant} FCFA — {self.salaire}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.salaire.update_statut()
