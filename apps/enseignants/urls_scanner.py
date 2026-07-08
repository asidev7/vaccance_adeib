from django.urls import path
from . import views_scanner

app_name = 'scanner'

urlpatterns = [
    path('', views_scanner.scanner, name='scanner'),
    path('api/enregistrer/', views_scanner.api_enregistrer_presence, name='api_enregistrer_presence'),
    path('api/valider/', views_scanner.api_valider_presence, name='api_valider_presence'),
]
