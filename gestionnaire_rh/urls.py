"""
URL configuration for gestionnaire_rh project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('employes/', include('employes.urls')),
    path('paie/', include('paie.urls')),
    path('temps/', include('temps_travail.urls')),
    path('conges/', include('conges.urls')),
    path('recrutement/', include('recrutement.urls')),
    path('formation/', include('formation.urls')),
    path('payments/', include('payments.urls')),
    path('portail/', include('portail.urls')),
    path('comptabilite/', include('comptabilite.urls')),
    # path('api/', include('api.urls')),  # TODO: Create api app
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customisation de l'admin
admin.site.site_header = "Gestionnaire RH Guinée"
admin.site.site_title = "Administration RH"
admin.site.index_title = "Bienvenue dans l'administration RH"
