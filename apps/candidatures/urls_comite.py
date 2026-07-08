from django.urls import path
from . import views_comite

app_name = 'candidatures_comite'

urlpatterns = [
    path('', views_comite.liste, name='liste_comite'),
    path('<int:id>/', views_comite.detail, name='detail_comite'),
    path('<int:id>/accepter/', views_comite.accepter, name='accepter_comite'),
    path('<int:id>/refuser/', views_comite.refuser, name='refuser_comite'),
]
