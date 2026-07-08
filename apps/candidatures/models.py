from django.db import models
from django.conf import settings


class CandidatureEnseignant(models.Model):
    NIVEAU_ETUDE_CHOICES = [
        ('BAC', 'Baccalauréat'),
        ('LICENCE1', 'Licence 1'),
        ('LICENCE2', 'Licence 2'),
        ('LICENCE3', 'Licence 3'),
        ('MASTER1', 'Master 1'),
        ('MASTER2', 'Master 2'),
        ('DOCTORAT', 'Doctorat'),
        ('AUTRE', 'Autre'),
    ]

    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('ACCEPTE', 'Acceptée'),
        ('REFUSE', 'Refusée'),
    ]

    nom_complet = models.CharField(max_length=200, verbose_name='Nom complet')
    telephone = models.CharField(max_length=20, verbose_name='Téléphone')
    email = models.EmailField(blank=True, verbose_name='Email')
    date_naissance = models.DateField(verbose_name='Date de naissance')
    niveau_etude = models.CharField(
        max_length=20,
        choices=NIVEAU_ETUDE_CHOICES,
        verbose_name='Niveau d\'études'
    )
    matieres_souhaitees = models.ManyToManyField(
        'emploi_du_temps.Matiere',
        verbose_name='Matières souhaitées'
    )
    experience = models.TextField(blank=True, verbose_name='Expérience')
    cv_fichier = models.FileField(
        upload_to='cv_candidatures/',
        blank=True,
        null=True,
        verbose_name='CV (fichier)'
    )
    motivation = models.TextField(verbose_name='Lettre de motivation')
    statut = models.CharField(
        max_length=15,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE',
        verbose_name='Statut'
    )
    date_soumission = models.DateTimeField(auto_now_add=True, verbose_name='Date de soumission')
    traite_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='candidatures_traitees',
        verbose_name='Traité par'
    )
    date_traitement = models.DateTimeField(null=True, blank=True, verbose_name='Date de traitement')

    class Meta:
        verbose_name = 'Candidature enseignant'
        verbose_name_plural = 'Candidatures enseignants'
        ordering = ['-date_soumission']

    def __str__(self):
        return f'Candidature de {self.nom_complet} ({self.get_statut_display()})'
