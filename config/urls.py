from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Public
    path('', include('apps.core.urls')),
    path('inscription/', include('apps.inscriptions.urls_public')),
    path('', include('apps.candidatures.urls_public')),
    # Comité
    path('comite/', include('apps.accounts.urls_comite')),
    path('comite/', include('apps.core.urls_comite')),
    path('comite/inscriptions/', include('apps.inscriptions.urls_comite')),
    path('comite/candidatures/', include('apps.candidatures.urls_comite')),
    path('comite/enseignants/', include('apps.enseignants.urls_comite')),
    path('comite/scanner/', include('apps.enseignants.urls_scanner')),
    path('comite/emploi-du-temps/', include('apps.emploi_du_temps.urls_comite')),
    path('comite/matieres/', include('apps.emploi_du_temps.urls_matieres')),
    path('comite/niveaux/', include('apps.emploi_du_temps.urls_niveaux')),
    path('comite/depenses/', include('apps.finances.urls_depenses')),
    path('comite/salaires/', include('apps.finances.urls_salaires')),
    path('comite/rapports/', include('apps.finances.urls_rapports')),
    # Enseignant
    path('enseignant/', include('apps.accounts.urls_enseignant')),
    path('enseignant/', include('apps.enseignants.urls_enseignant')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
