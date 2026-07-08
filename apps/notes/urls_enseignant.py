from django.urls import path
from . import views_enseignant

app_name = 'notes_enseignant'

urlpatterns = [
    path('notes/', views_enseignant.liste_classes, name='liste_classes'),
    path('notes/<int:niveau_id>/', views_enseignant.saisie_notes, name='saisie_notes'),
]
