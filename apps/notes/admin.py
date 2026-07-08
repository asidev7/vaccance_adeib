from django.contrib import admin
from .models import CoefficientMatiere, Note, BulletinConfig, BulletinGenere


@admin.register(CoefficientMatiere)
class CoefficientMatiereAdmin(admin.ModelAdmin):
    list_display = ['matiere', 'niveau', 'coefficient']
    list_filter = ['niveau', 'matiere__niveau_concerne']
    search_fields = ['matiere__nom', 'niveau__nom']


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['inscription', 'matiere', 'note', 'coefficient', 'enseignant', 'session']
    list_filter = ['session', 'matiere']
    search_fields = ['inscription__nom_eleve', 'inscription__prenom_eleve', 'matiere__nom']


@admin.register(BulletinConfig)
class BulletinConfigAdmin(admin.ModelAdmin):
    list_display = ['niveau', 'session', 'saisie_ouverte', 'bulletin_generable']
    list_filter = ['session', 'saisie_ouverte']


@admin.register(BulletinGenere)
class BulletinGenereAdmin(admin.ModelAdmin):
    list_display = ['inscription', 'session', 'genere_le', 'genere_par']
    list_filter = ['session', 'genere_le']
