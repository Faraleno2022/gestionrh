from django.urls import path
from . import views

app_name = 'temps_travail'

urlpatterns = [
    # Accueil
    path('', views.temps_travail_home, name='home'),
    
    # Pointages
    path('pointages/', views.liste_pointages, name='pointages'),
    path('pointages/creer/', views.creer_pointage, name='creer_pointage'),
    path('pointages/pointer-entree/', views.pointer_entree, name='pointer_entree'),
    path('pointages/pointer-sortie/', views.pointer_sortie, name='pointer_sortie'),
    
    # Congés
    path('conges/', views.liste_conges, name='conges'),
    path('conges/creer/', views.creer_conge, name='creer_conge'),
    path('conges/<int:pk>/approuver/', views.approuver_conge, name='approuver_conge'),
    
    # Absences
    path('absences/', views.liste_absences, name='absences'),
    path('absences/creer/', views.creer_absence, name='creer_absence'),
    
    # Jours fériés
    path('jours-feries/', views.liste_jours_feries, name='liste_jours_feries'),
    path('jours-feries/creer/', views.creer_jour_ferie, name='creer_jour_ferie'),
    
    # Rapports
    path('rapports/presence/', views.rapport_presence, name='rapport_presence'),
    path('rapports/heures-supplementaires/', views.rapport_heures_supplementaires, name='rapport_heures_supplementaires'),
]
