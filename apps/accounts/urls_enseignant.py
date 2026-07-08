from django.urls import path
from . import views

app_name = 'accounts_enseignant'

urlpatterns = [
    path('login/', views.enseignant_login, name='enseignant_login'),
    path('logout/', views.enseignant_logout, name='enseignant_logout'),
]
