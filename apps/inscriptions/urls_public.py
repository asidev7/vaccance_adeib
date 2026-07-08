from django.urls import path
from . import views_public

app_name = 'inscriptions'

urlpatterns = [
    path('', views_public.formulaire_inscription, name='formulaire_public'),
]
