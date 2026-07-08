from django.contrib import admin
from .models import Depense, Salaire, VersementSalaire


@admin.register(Depense)
class DepenseAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'categorie', 'montant', 'date_depense')
    list_filter = ('categorie', 'date_depense')
    search_fields = ('libelle',)


@admin.register(Salaire)
class SalaireAdmin(admin.ModelAdmin):
    list_display = ('enseignant', 'session', 'nombre_heures_effectuees', 'montant_brut', 'montant_deja_verse', 'statut')
    list_filter = ('statut', 'session')
    search_fields = ('enseignant__user__first_name', 'enseignant__user__last_name')
    readonly_fields = ('date_calcul',)


@admin.register(VersementSalaire)
class VersementSalaireAdmin(admin.ModelAdmin):
    list_display = ('salaire', 'montant', 'mode_paiement', 'date_versement')
    list_filter = ('mode_paiement', 'date_versement')
