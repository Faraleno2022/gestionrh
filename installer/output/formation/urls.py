from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'formation'

urlpatterns = [
    # Accueil
    path('', views.formation_home, name='home'),
    
    # Redirection ancienne URL
    path('list/', RedirectView.as_view(pattern_name='formation:catalogue', permanent=True)),
    
    # Catalogue
    path('catalogue/', views.liste_catalogue, name='catalogue'),
    path('catalogue/creer/', views.creer_formation, name='creer_formation'),
    path('catalogue/<int:pk>/', views.detail_formation, name='detail_formation'),
    path('catalogue/<int:pk>/modifier/', views.modifier_formation, name='modifier_formation'),
    
    # Sessions
    path('sessions/', views.liste_sessions, name='sessions'),
    path('sessions/planifier/', views.planifier_session, name='planifier_session'),
    path('sessions/<int:pk>/', views.detail_session, name='detail_session'),
    path('sessions/<int:session_id>/inscrire/', views.inscrire_employe, name='inscrire_employe'),
    
    # Inscriptions
    path('inscriptions/', views.liste_inscriptions, name='inscriptions'),
    path('inscriptions/<int:pk>/evaluer/', views.evaluer_participant, name='evaluer_participant'),
    
    # Évaluations
    path('evaluations/', views.liste_evaluations, name='evaluations'),
    path('evaluations/creer/<int:inscription_id>/', views.formulaire_evaluation, name='formulaire_evaluation'),
    
    # Plan de formation
    path('plan/', views.liste_plans, name='plans'),
    path('plan/creer/', views.creer_plan, name='creer_plan'),
    path('plan/<int:annee>/', views.detail_plan, name='detail_plan'),
]
