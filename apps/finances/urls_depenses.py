from django.urls import path
from . import views_depenses

app_name = 'depenses'

urlpatterns = [
    path('', views_depenses.liste, name='liste'),
    path('ajouter/', views_depenses.ajouter, name='ajouter'),
    path('<int:id>/modifier/', views_depenses.modifier, name='modifier'),
]
