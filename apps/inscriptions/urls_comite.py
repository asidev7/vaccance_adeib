from django.urls import path
from . import views_comite

app_name = 'inscriptions_comite'

urlpatterns = [
    path('', views_comite.liste, name='liste_comite'),
    path('ajouter/', views_comite.ajouter, name='ajouter_comite'),
    path('<int:id>/', views_comite.detail, name='detail_comite'),
    path('<int:id>/paiement/', views_comite.paiement_ajout, name='paiement_ajout_comite'),
]
