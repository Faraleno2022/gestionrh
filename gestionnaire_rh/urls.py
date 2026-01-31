"""
URL configuration for gestionnaire_rh project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import HttpResponse

def robots_txt(request):
    content = """# Robots.txt pour GuinéeRH
User-agent: *
Allow: /
Allow: /login/
Allow: /inscription/
Disallow: /admin/
Disallow: /api/
Disallow: /employes/
Disallow: /paie/
Disallow: /conges/
Disallow: /core/
Disallow: /comptabilite/
Sitemap: https://www.guineerh.space/sitemap.xml
"""
    return HttpResponse(content, content_type="text/plain")

def sitemap_xml(request):
    content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://www.guineerh.space/</loc>
        <changefreq>weekly</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://www.guineerh.space/login/</loc>
        <changefreq>monthly</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>https://www.guineerh.space/inscription/</loc>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://www.guineerh.space/documentation-legale/</loc>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
</urlset>"""
    return HttpResponse(content, content_type="application/xml")

def google_verification(request):
    return HttpResponse("google-site-verification: google47b11a2550ab2dda.html", content_type="text/html")

urlpatterns = [
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap_xml, name='sitemap_xml'),
    path('google47b11a2550ab2dda.html', google_verification, name='google_verification'),
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
    path('contrats/', include('contrats.urls')),
    # path('api/', include('api.urls')),  # TODO: Create api app
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customisation de l'admin
admin.site.site_header = "Gestionnaire RH Guinée"
admin.site.site_title = "Administration RH"
admin.site.index_title = "Bienvenue dans l'administration RH"
