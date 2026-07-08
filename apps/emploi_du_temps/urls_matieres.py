from django.urls import path
from . import views_matieres

app_name = 'matieres'

urlpatterns = [
    path('', views_matieres.liste, name='liste'),
    path('ajouter/', views_matieres.ajouter, name='ajouter'),
    path('<int:id>/modifier/', views_matieres.modifier, name='modifier'),
    path('<int:id>/supprimer/', views_matieres.supprimer, name='supprimer'),
]
