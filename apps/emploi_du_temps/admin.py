from django.contrib import admin
from .models import Matiere, Niveau, EmploiDuTemps


@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ('nom', 'niveau_concerne', 'couleur_badge')
    list_filter = ('niveau_concerne',)
    search_fields = ('nom',)


@admin.register(Niveau)
class NiveauAdmin(admin.ModelAdmin):
    list_display = ('nom', 'cycle')
    list_filter = ('cycle',)
    search_fields = ('nom',)


@admin.register(EmploiDuTemps)
class EmploiDuTempsAdmin(admin.ModelAdmin):
    list_display = ('session', 'jour', 'heure_debut', 'heure_fin', 'matiere', 'niveau', 'enseignant', 'salle')
    list_filter = ('session', 'jour', 'niveau__cycle')
    search_fields = ('matiere__nom', 'enseignant__user__first_name', 'salle')
