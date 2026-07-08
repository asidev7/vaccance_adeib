from django.urls import path
from . import views_comite

app_name = 'core_comite'

urlpatterns = [
    path('dashboard/', views_comite.dashboard, name='dashboard_comite'),
]
