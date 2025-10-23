from django.urls import path
from . import views

app_name = 'paie'

urlpatterns = [
    # Accueil
    path('', views.paie_home, name='home'),
    
    # Périodes de paie
    path('periodes/', views.liste_periodes, name='liste_periodes'),
    path('periodes/creer/', views.creer_periode, name='creer_periode'),
    path('periodes/<int:pk>/', views.detail_periode, name='detail_periode'),
    path('periodes/<int:pk>/calculer/', views.calculer_periode, name='calculer_periode'),
    path('periodes/<int:pk>/valider/', views.valider_periode, name='valider_periode'),
    path('periodes/<int:pk>/cloturer/', views.cloturer_periode, name='cloturer_periode'),
    
    # Bulletins de paie
    path('bulletins/', views.liste_bulletins, name='liste_bulletins'),
    path('bulletins/<int:pk>/', views.detail_bulletin, name='detail_bulletin'),
    path('bulletins/<int:pk>/imprimer/', views.imprimer_bulletin, name='imprimer_bulletin'),
    
    # Livre de paie
    path('livre/', views.livre_paie, name='livre_paie'),
    
    # Déclarations sociales
    path('declarations/', views.declarations_sociales, name='declarations_sociales'),
    
    # Éléments de salaire
    path('elements-salaire/', views.liste_elements_salaire, name='liste_elements_salaire'),
    path('elements-salaire/employe/<int:employe_id>/', views.elements_salaire_employe, name='elements_salaire_employe'),
    path('elements-salaire/ajouter/<int:employe_id>/', views.ajouter_element_salaire, name='ajouter_element_salaire'),
    path('elements-salaire/<int:pk>/modifier/', views.modifier_element_salaire, name='modifier_element_salaire'),
    path('elements-salaire/<int:pk>/supprimer/', views.supprimer_element_salaire, name='supprimer_element_salaire'),
    
    # Rubriques de paie
    path('rubriques/', views.liste_rubriques, name='liste_rubriques'),
    path('rubriques/creer/', views.creer_rubrique, name='creer_rubrique'),
    path('rubriques/<int:pk>/', views.detail_rubrique, name='detail_rubrique'),
]
