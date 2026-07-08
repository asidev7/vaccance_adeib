from django.db import models
from django.conf import settings


class Inscription(models.Model):
    STATUT_PAIEMENT_CHOICES = [
        ('IMPAYE', 'Impayé'),
        ('PARTIEL', 'Partiel'),
        ('PAYE', 'Payé'),
    ]

    nom_eleve = models.CharField(max_length=100, verbose_name='Nom de l\'élève')
    prenom_eleve = models.CharField(max_length=100, verbose_name='Prénom de l\'élève')
    date_naissance = models.DateField(verbose_name='Date de naissance')
    niveau = models.ForeignKey(
        'emploi_du_temps.Niveau',
        on_delete=models.CASCADE,
        related_name='inscriptions',
        verbose_name='Niveau / Classe'
    )
    matieres_choisies = models.ManyToManyField(
        'emploi_du_temps.Matiere',
        verbose_name='Matières choisies'
    )
    nom_parent = models.CharField(max_length=200, verbose_name='Nom du parent / tuteur')
    telephone_parent = models.CharField(max_length=20, verbose_name='Téléphone du parent')
    session = models.ForeignKey(
        'core.SessionVacances',
        on_delete=models.CASCADE,
        related_name='inscriptions',
        verbose_name='Session'
    )
    date_inscription = models.DateTimeField(auto_now_add=True, verbose_name='Date d\'inscription')
    statut_paiement = models.CharField(
        max_length=10,
        choices=STATUT_PAIEMENT_CHOICES,
        default='IMPAYE',
        verbose_name='Statut du paiement'
    )
    montant_du = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        verbose_name='Montant dû (FCFA)'
    )
    montant_paye = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        verbose_name='Montant payé (FCFA)'
    )

    class Meta:
        verbose_name = 'Inscription élève'
        verbose_name_plural = 'Inscriptions élèves'
        ordering = ['-date_inscription']

    def __str__(self):
        return f'{self.nom_eleve} {self.prenom_eleve} — {self.niveau}'

    def calculer_montant_paye(self):
        """Recalculate montant_paye from confirmed payments."""
        total = self.paiements.filter(statut='CONFIRME').aggregate(
            total=models.Sum('montant')
        )['total'] or 0
        self.montant_paye = total
        if total >= self.montant_du:
            self.statut_paiement = 'PAYE'
        elif total > 0:
            self.statut_paiement = 'PARTIEL'
        else:
            self.statut_paiement = 'IMPAYE'
        self.save(update_fields=['montant_paye', 'statut_paiement'])


class Paiement(models.Model):
    METHODE_CHOICES = [
        ('ESPECES', 'Espèces'),
        ('FEDAPAY_MOBILE_MONEY', 'FedaPay Mobile Money'),
    ]

    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('CONFIRME', 'Confirmé'),
        ('ECHOUE', 'Échoué'),
    ]

    inscription = models.ForeignKey(
        Inscription,
        on_delete=models.CASCADE,
        related_name='paiements',
        verbose_name='Inscription'
    )
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        verbose_name='Montant (FCFA)'
    )
    methode = models.CharField(
        max_length=25,
        choices=METHODE_CHOICES,
        verbose_name='Méthode de paiement'
    )
    reference_fedapay = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Référence FedaPay'
    )
    date_paiement = models.DateTimeField(auto_now_add=True, verbose_name='Date de paiement')
    enregistre_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paiements_enregistres',
        verbose_name='Enregistré par'
    )
    statut = models.CharField(
        max_length=15,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE',
        verbose_name='Statut'
    )

    class Meta:
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'
        ordering = ['-date_paiement']

    def __str__(self):
        return f'{self.montant} FCFA — {self.inscription} ({self.get_statut_display()})'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update inscription montant_paye when payment is confirmed
        if self.statut == 'CONFIRME':
            self.inscription.calculer_montant_paye()
