from django.urls import path
from . import views_enseignant

app_name = 'enseignant'

urlpatterns = [
    path('dashboard/', views_enseignant.dashboard, name='dashboard'),
    path('mon-qrcode/', views_enseignant.mon_qrcode, name='mon_qrcode'),
    path('presences/', views_enseignant.mes_presences, name='mes_presences'),
    path('salaires/', views_enseignant.mes_salaires, name='mes_salaires'),
    path('profil/', views_enseignant.profil, name='profil'),
    path('salaires/<int:salaire_id>/bulletin/', views_enseignant.bulletin_pdf, name='bulletin_pdf'),
]
