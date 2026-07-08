from django.contrib import admin
from .models import CandidatureEnseignant


@admin.register(CandidatureEnseignant)
class CandidatureEnseignantAdmin(admin.ModelAdmin):
    list_display = ('nom_complet', 'telephone', 'niveau_etude', 'statut', 'date_soumission')
    list_filter = ('statut', 'niveau_etude', 'date_soumission')
    search_fields = ('nom_complet', 'telephone', 'email')
    readonly_fields = ('date_soumission',)
