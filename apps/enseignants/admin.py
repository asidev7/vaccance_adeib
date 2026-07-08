from django.contrib import admin
from .models import Enseignant, Presence


@admin.register(Enseignant)
class EnseignantAdmin(admin.ModelAdmin):
    list_display = ('user', 'taux_horaire', 'est_actif', 'date_activation')
    list_filter = ('est_actif',)
    search_fields = ('user__first_name', 'user__last_name', 'user__username')
    readonly_fields = ('qr_code_uid', 'qr_code_image', 'date_activation')


@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ('enseignant', 'creneau', 'date', 'statut', 'heure_scan')
    list_filter = ('statut', 'date')
    search_fields = ('enseignant__user__first_name', 'enseignant__user__last_name')
