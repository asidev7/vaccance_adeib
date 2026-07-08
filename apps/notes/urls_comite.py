from django.urls import path
from . import views_comite

app_name = 'notes_comite'

urlpatterns = [
    path('bulletins/config/', views_comite.config_bulletins, name='config_bulletins'),
    path('bulletins/niveau/<int:niveau_id>/', views_comite.liste_eleves_notes, name='liste_eleves_notes'),
    path('bulletins/niveau/<int:niveau_id>/generer/', views_comite.liste_eleves_generation, name='generer_bulletins'),
    path('bulletins/niveau/<int:niveau_id>/coefficients/', views_comite.coefficients_matiere, name='coefficients'),
    path('bulletins/niveau/<int:niveau_id>/saisie/', views_comite.saisie_notes_admin, name='saisie_notes_admin'),
    path('bulletins/telecharger/<int:bulletin_id>/', views_comite.telecharger_bulletin, name='telecharger_bulletin'),
    path('bulletins/generes/', views_comite.bulletins_generes, name='bulletins_generes'),
    path('bulletins/generer-tous/', views_comite.generer_tous_bulletins, name='generer_tous_bulletins'),
]
