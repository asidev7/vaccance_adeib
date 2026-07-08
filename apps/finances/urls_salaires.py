from django.urls import path
from . import views_salaires

app_name = 'salaires'

urlpatterns = [
    path('', views_salaires.liste, name='liste'),
    path('calculer/', views_salaires.calculer, name='calculer'),
    path('<int:id>/', views_salaires.detail, name='detail'),
    path('<int:id>/versement/', views_salaires.versement_ajout, name='versement_ajout'),
    path('<int:id>/bulletin/', views_salaires.bulletin_pdf, name='bulletin_pdf'),
]
