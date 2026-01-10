from django.urls import path
from . import views

app_name = 'comptabilite'

urlpatterns = [
    # Dashboard comptabilité
    path('', views.dashboard, name='dashboard'),
    
    # Plan comptable
    path('plan-comptable/', views.plan_comptable_list, name='plan_comptable_list'),
    path('plan-comptable/ajouter/', views.plan_comptable_create, name='plan_comptable_create'),
    path('plan-comptable/<int:pk>/', views.plan_comptable_detail, name='plan_comptable_detail'),
    path('plan-comptable/<int:pk>/modifier/', views.plan_comptable_update, name='plan_comptable_update'),
    
    # Journaux
    path('journaux/', views.journal_list, name='journal_list'),
    path('journaux/ajouter/', views.journal_create, name='journal_create'),
    path('journaux/<int:pk>/modifier/', views.journal_update, name='journal_update'),
    
    # Exercices comptables
    path('exercices/', views.exercice_list, name='exercice_list'),
    path('exercices/ajouter/', views.exercice_create, name='exercice_create'),
    path('exercices/<int:pk>/modifier/', views.exercice_update, name='exercice_update'),
    
    # Écritures comptables
    path('ecritures/', views.ecriture_list, name='ecriture_list'),
    path('ecritures/ajouter/', views.ecriture_create, name='ecriture_create'),
    path('ecritures/<uuid:pk>/', views.ecriture_detail, name='ecriture_detail'),
    path('ecritures/<uuid:pk>/modifier/', views.ecriture_update, name='ecriture_update'),
    path('ecritures/<uuid:pk>/valider/', views.ecriture_valider, name='ecriture_valider'),
    
    # Tiers (clients/fournisseurs)
    path('tiers/', views.tiers_list, name='tiers_list'),
    path('tiers/ajouter/', views.tiers_create, name='tiers_create'),
    path('tiers/<uuid:pk>/', views.tiers_detail, name='tiers_detail'),
    path('tiers/<uuid:pk>/modifier/', views.tiers_update, name='tiers_update'),
    
    # Factures
    path('factures/', views.facture_list, name='facture_list'),
    path('factures/ajouter/', views.facture_create, name='facture_create'),
    path('factures/<uuid:pk>/', views.facture_detail, name='facture_detail'),
    path('factures/<uuid:pk>/modifier/', views.facture_update, name='facture_update'),
    path('factures/<uuid:pk>/valider/', views.facture_valider, name='facture_valider'),
    path('factures/<uuid:pk>/imprimer/', views.facture_print, name='facture_print'),
    
    # Règlements
    path('reglements/', views.reglement_list, name='reglement_list'),
    path('reglements/ajouter/', views.reglement_create, name='reglement_create'),
    path('reglements/<uuid:pk>/', views.reglement_detail, name='reglement_detail'),
    
    # États financiers
    path('etats/grand-livre/', views.grand_livre, name='grand_livre'),
    path('etats/grand-livre/pdf/', views.grand_livre_pdf, name='grand_livre_pdf'),
    path('etats/grand-livre/excel/', views.grand_livre_excel, name='grand_livre_excel'),
    path('etats/balance/', views.balance, name='balance'),
    path('etats/balance/pdf/', views.balance_pdf, name='balance_pdf'),
    path('etats/balance/excel/', views.balance_excel, name='balance_excel'),
    path('etats/journal-general/', views.journal_general, name='journal_general'),
    path('etats/journal-general/pdf/', views.journal_general_pdf, name='journal_general_pdf'),
    path('etats/journal-general/excel/', views.journal_general_excel, name='journal_general_excel'),
    path('etats/bilan/', views.bilan, name='bilan'),
    path('etats/bilan/pdf/', views.bilan_pdf, name='bilan_pdf'),
    path('etats/bilan/excel/', views.bilan_excel, name='bilan_excel'),
    path('etats/compte-resultat/', views.compte_resultat, name='compte_resultat'),
    path('etats/compte-resultat/pdf/', views.compte_resultat_pdf, name='compte_resultat_pdf'),
    path('etats/compte-resultat/excel/', views.compte_resultat_excel, name='compte_resultat_excel'),
    
    # Clients & Fournisseurs détaillés
    path('clients/', views.compte_client_list, name='compte_client_list'),
    path('clients/<uuid:pk>/', views.compte_client_detail, name='compte_client_detail'),
    path('clients/vieillissement/', views.vieillissement_creances, name='vieillissement_creances'),
    path('clients/impayes/', views.impayes_clients, name='impayes_clients'),
    path('fournisseurs/', views.compte_fournisseur_list, name='compte_fournisseur_list'),
    path('fournisseurs/<uuid:pk>/', views.compte_fournisseur_detail, name='compte_fournisseur_detail'),
    path('fournisseurs/vieillissement/', views.vieillissement_dettes, name='vieillissement_dettes'),
    path('fournisseurs/impayes/', views.impayes_fournisseurs, name='impayes_fournisseurs'),
]
