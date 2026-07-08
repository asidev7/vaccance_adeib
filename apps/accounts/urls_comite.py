from django.urls import path
from . import views

app_name = 'accounts_comite'

urlpatterns = [
    path('login/', views.comite_login, name='comite_login'),
    path('logout/', views.comite_logout, name='comite_logout'),
]
