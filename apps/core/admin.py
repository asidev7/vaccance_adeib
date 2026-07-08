from django.contrib import admin
from .models import SessionVacances


@admin.register(SessionVacances)
class SessionVacancesAdmin(admin.ModelAdmin):
    list_display = ('nom', 'annee', 'date_debut', 'date_fin', 'est_active', 'frais_inscription')
    list_filter = ('est_active', 'annee')
    search_fields = ('nom',)
