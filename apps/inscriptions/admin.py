from django.contrib import admin
from .models import Inscription, Paiement


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ('nom_eleve', 'prenom_eleve', 'niveau', 'session', 'statut_paiement', 'montant_du', 'montant_paye')
    list_filter = ('statut_paiement', 'niveau', 'session')
    search_fields = ('nom_eleve', 'prenom_eleve', 'nom_parent', 'telephone_parent')
    readonly_fields = ('date_inscription', 'montant_paye')


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('inscription', 'montant', 'methode', 'statut', 'date_paiement')
    list_filter = ('statut', 'methode', 'date_paiement')
    search_fields = ('inscription__nom_eleve', 'reference_fedapay')
