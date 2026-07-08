from django.urls import path
from . import views_comite

app_name = 'enseignants_comite'

urlpatterns = [
    path('', views_comite.liste, name='liste_comite'),
    path('ajouter/', views_comite.ajouter_enseignant, name='ajouter_enseignant'),
    path('<int:id>/', views_comite.detail, name='detail_comite'),
    path('<int:id>/desactiver/', views_comite.desactiver, name='desactiver_comite'),
]
