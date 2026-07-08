from django.urls import path
from . import views_niveaux

app_name = 'niveaux'

urlpatterns = [
    path('', views_niveaux.liste, name='liste'),
    path('ajouter/', views_niveaux.ajouter, name='ajouter'),
    path('<int:id>/modifier/', views_niveaux.modifier, name='modifier'),
    path('<int:id>/supprimer/', views_niveaux.supprimer, name='supprimer'),
]
