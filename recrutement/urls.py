from django.urls import path
from . import views
from . import views_public

app_name = 'recrutement'

urlpatterns = [
    # Accueil
    path('', views.recrutement_home, name='home'),
    
    # Vues publiques (sans authentification)
    path('offre/<int:pk>/', views_public.offre_detail_public, name='offre_public'),
    path('offre/<int:pk>/postuler/', views_public.postuler, name='postuler'),
    path('candidature/confirmation/<str:numero>/', views_public.candidature_confirmee, name='candidature_confirmee'),
    
    # Offres d'emploi
    path('offres/', views.liste_offres, name='offres'),
    path('offres/creer/', views.creer_offre, name='creer_offre'),
    path('offres/<int:pk>/', views.detail_offre, name='detail_offre'),
    path('offres/<int:pk>/modifier/', views.modifier_offre, name='modifier_offre'),
    
    # Candidatures
    path('candidatures/', views.liste_candidatures, name='candidatures'),
    path('candidatures/creer/', views.creer_candidature, name='creer_candidature'),
    path('candidatures/<int:pk>/', views.detail_candidature, name='detail_candidature'),
    path('candidatures/<int:pk>/evaluer/', views.evaluer_candidature, name='evaluer_candidature'),
    
    # Entretiens
    path('entretiens/', views.liste_entretiens, name='entretiens'),
    path('entretiens/creer/<int:candidature_id>/', views.creer_entretien, name='creer_entretien'),
    path('entretiens/<int:pk>/', views.detail_entretien, name='detail_entretien'),
    path('entretiens/<int:pk>/evaluer/', views.evaluer_entretien, name='evaluer_entretien'),
]
