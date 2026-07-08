from django.urls import path
from . import views_public

app_name = 'candidatures'

urlpatterns = [
    path('devenir-enseignant/', views_public.formulaire, name='formulaire_public'),
    path('suivi-candidature/', views_public.suivi, name='suivi'),
]
