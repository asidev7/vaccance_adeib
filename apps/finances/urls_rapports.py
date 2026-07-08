from django.urls import path
from . import views_rapports

app_name = 'rapports'

urlpatterns = [
    path('', views_rapports.index, name='index'),
    path('bilan-pdf/', views_rapports.bilan_pdf, name='bilan_pdf'),
    path('presences-excel/', views_rapports.presences_excel, name='presences_excel'),
]
