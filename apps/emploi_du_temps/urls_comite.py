from django.urls import path
from . import views_comite

app_name = 'emploi_du_temps_comite'

urlpatterns = [
    path('', views_comite.grille, name='grille_comite'),
    path('ajouter/', views_comite.creneau_ajout, name='creneau_ajout_comite'),
    path('<int:id>/modifier/', views_comite.creneau_modifier, name='creneau_modifier_comite'),
]
