from django.urls import path
from . import views

app_name = 'portail'

urlpatterns = [
    # Accueil
    path('', views.portail_accueil, name='accueil'),
    
    # Bulletins de paie
    path('bulletins/', views.mes_bulletins, name='mes_bulletins'),
    path('bulletins/<int:pk>/', views.detail_bulletin, name='detail_bulletin'),
    
    # Congés
    path('conges/', views.mes_conges, name='mes_conges'),
    path('conges/demander/', views.demander_conge, name='demander_conge'),
    path('conges/<int:pk>/annuler/', views.annuler_conge, name='annuler_conge'),
    
    # Prêts
    path('prets/', views.mes_prets, name='mes_prets'),
    path('prets/<int:pk>/', views.detail_pret, name='detail_pret'),
    path('prets/demander/', views.demander_pret, name='demander_pret'),
    
    # Heures supplémentaires
    path('heures-sup/', views.mes_heures_sup, name='mes_heures_sup'),
    
    # Profil
    path('profil/', views.mon_profil, name='mon_profil'),
]
