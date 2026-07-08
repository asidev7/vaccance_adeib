import uuid
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.db import models
from django.conf import settings


def qr_code_upload_path(instance, filename):
    return f'qr_codes/enseignant_{instance.qr_code_uid}.png'


class Enseignant(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enseignant',
        verbose_name='Utilisateur'
    )
    candidature_origine = models.ForeignKey(
        'candidatures.CandidatureEnseignant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enseignant_cree',
        verbose_name='Candidature d\'origine'
    )
    matieres = models.ManyToManyField(
        'emploi_du_temps.Matiere',
        verbose_name='Matières enseignées'
    )
    qr_code_uid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='UID du QR code'
    )
    qr_code_image = models.ImageField(
        upload_to=qr_code_upload_path,
        blank=True,
        null=True,
        verbose_name='Image du QR code'
    )
    taux_horaire = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=1000,
        verbose_name='Taux horaire (FCFA)'
    )
    date_activation = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date d\'activation'
    )
    est_actif = models.BooleanField(default=True, verbose_name='Enseignant actif')

    class Meta:
        verbose_name = 'Enseignant'
        verbose_name_plural = 'Enseignants'
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new or not self.qr_code_image:
            self._generate_qr_code()

    def _generate_qr_code(self):
        """Generate QR code image containing the UID."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(str(self.qr_code_uid))
        qr.make(fit=True)

        img = qr.make_image(fill_color='#0048AE', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        filename = f'qr_enseignant_{self.qr_code_uid}.png'

        self.qr_code_image.save(filename, ContentFile(buffer.getvalue()), save=True)

    @property
    def nombre_heures_planifiees(self):
        """Total planned hours for the active session."""
        from apps.core.models import SessionVacances
        session = SessionVacances.objects.filter(est_active=True).first()
        if not session:
            return 0
        from datetime import datetime, time
        creneaux = self.creneaux.filter(session=session)
        total_minutes = 0
        for c in creneaux:
            debut = datetime.combine(session.date_debut, c.heure_debut)
            fin = datetime.combine(session.date_debut, c.heure_fin)
            total_minutes += (fin - debut).total_seconds() / 60
        return total_minutes / 60


class Presence(models.Model):
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente de validation'),
        ('PRESENT', 'Présent (validé)'),
        ('RETARD', 'Retard (validé)'),
        ('ABSENT', 'Absent'),
    ]

    enseignant = models.ForeignKey(
        Enseignant,
        on_delete=models.CASCADE,
        related_name='presences',
        verbose_name='Enseignant'
    )
    creneau = models.ForeignKey(
        'emploi_du_temps.EmploiDuTemps',
        on_delete=models.CASCADE,
        related_name='presences',
        verbose_name='Créneau'
    )
    date = models.DateField(verbose_name='Date')
    heure_scan = models.DateTimeField(auto_now_add=True, verbose_name='Heure du scan')
    statut = models.CharField(
        max_length=15,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE',
        verbose_name='Statut'
    )
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='presences_validees',
        verbose_name='Validé par'
    )
    commentaire = models.TextField(blank=True, verbose_name='Commentaire')

    class Meta:
        verbose_name = 'Présence'
        verbose_name_plural = 'Présences'
        ordering = ['-date', '-heure_scan']
        constraints = [
            models.UniqueConstraint(
                fields=['enseignant', 'creneau', 'date'],
                name='unique_presence_par_creneau_jour'
            ),
        ]

    def __str__(self):
        return f'{self.enseignant} — {self.creneau} — {self.date} ({self.get_statut_display()})'
