from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrateur'
        TRESORIER = 'tresorier', 'Trésorier'
        SECRETAIRE = 'secretaire', 'Secrétaire'
        ENSEIGNANT = 'enseignant', 'Enseignant'

    STAFF_COMITE_ROLES = [Role.ADMIN, Role.TRESORIER, Role.SECRETAIRE]

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ADMIN,
        verbose_name='Rôle'
    )
    telephone = models.CharField(max_length=20, blank=True, verbose_name='Téléphone')
    photo = models.ImageField(
        upload_to='photos_utilisateurs/',
        blank=True,
        null=True,
        verbose_name='Photo de profil'
    )
    est_actif = models.BooleanField(default=True, verbose_name='Compte actif')

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    @property
    def is_staff_comite(self):
        """True if user is any comité staff (admin, tresorier, secretaire)."""
        return self.role in self.STAFF_COMITE_ROLES

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_tresorier(self):
        return self.role in (self.Role.ADMIN, self.Role.TRESORIER)

    @property
    def is_secretaire(self):
        return self.role in (self.Role.ADMIN, self.Role.SECRETAIRE)

    @property
    def is_enseignant(self):
        return self.role == self.Role.ENSEIGNANT
