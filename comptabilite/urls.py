"""
URLs for the Comptabilité module - Comprehensive routing
This file organizes URLs for accounting operations, bank reconciliation, 
fiscal declarations, and audit operations across multiple phases.

Pattern structure:
- CompteBancaire: comptes/
- RapprochementBancaire: rapprochements/
- OperationBancaire: operations/
- Utility endpoints: /importer/, /exporter/, /ajax/
- Dashboards: /tableau-de-bord/
"""

from django.urls import path
from . import views

app_name = 'comptabilite'

# ============================================================================
# RAPPROCHEMENTS BANCAIRES - Main Module for Phase 1
# ============================================================================

# Compte Bancaire URLs
compte_bancaire_patterns = [
    path('comptes/', views.CompteBancaireListView.as_view(), name='compte-bancaire-list'),
    path('comptes/nouveau/', views.CompteBancaireCreateView.as_view(), name='compte-bancaire-create'),
    path('comptes/<uuid:pk>/', views.CompteBancaireDetailView.as_view(), name='compte-bancaire-detail'),
    path('comptes/<uuid:pk>/editer/', views.CompteBancaireUpdateView.as_view(), name='compte-bancaire-update'),
    path('comptes/<uuid:pk>/supprimer/', views.CompteBancaireDeleteView.as_view(), name='compte-bancaire-delete'),
]

# Rapprochement Bancaire URLs
rapprochement_patterns = [
    path('rapprochements/', views.RapprochementListView.as_view(), name='rapprochement-list'),
    path('rapprochements/nouveau/', views.RapprochementCreateView.as_view(), name='rapprochement-create'),
    path('rapprochements/<uuid:pk>/', views.RapprochementDetailView.as_view(), name='rapprochement-detail'),
    path('rapprochements/<uuid:pk>/editer/', views.RapprochementUpdateView.as_view(), name='rapprochement-update'),
    path('rapprochements/<uuid:pk>/supprimer/', views.RapprochementDeleteView.as_view(), name='rapprochement-delete'),
    path('rapprochements/<uuid:pk>/finaliser/', views.RapprochementFinalisationView.as_view(), name='rapprochement-finalize'),
]

# Lettrage (Matching) URLs
lettrage_patterns = [
    path('rapprochements/<uuid:rapprochement_id>/lettrer/', views.LettrageView.as_view(), name='rapprochement-lettrage'),
    path('rapprochements/<uuid:rapprochement_id>/lettrage/<uuid:lettrage_id>/supprimer/', views.LettrageAnnulationView.as_view(), name='rapprochement-lettrage-delete'),
]

# ============================================================================
# IMPORT/EXPORT Operations
# ============================================================================

import_export_patterns = [
    # Import
    path('importer/', views.OperationImportView.as_view(), name='operation-import'),
]

# ============================================================================
# AJAX/API Endpoints
# ============================================================================

ajax_patterns = [
]

# ============================================================================
# DASHBOARDS & REPORTS
# ============================================================================

dashboard_report_patterns = [
    path('tableau-de-bord/', views.ComptabiliteDashboardView.as_view(), name='comptabilite-dashboard'),
    path('tableau-de-bord/rapprochements/', views.RapprochementDashboardView.as_view(), name='rapprochement-dashboard'),
    path('rapports/rapprochement/', views.RapprochementReportView.as_view(), name='rapprochement-report'),
    path('rapports/divergences/', views.DivergenceReportView.as_view(), name='divergence-report'),
    path('rapports/lettrage/', views.LettrageReportView.as_view(), name='lettrage-report'),
]

# ============================================================================
# LEGACY/EXISTING URLs (Keep for backward compatibility)
# ============================================================================

legacy_patterns = [
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

# ============================================================================
# COMBINED URL PATTERNS
# ============================================================================

urlpatterns = (
    # Phase 1: Rapprochements Bancaires (primary)
    rapprochement_patterns +
    compte_bancaire_patterns +
    lettrage_patterns +
    
    # Utilities
    import_export_patterns +
    ajax_patterns +
    dashboard_report_patterns +
    
    # Legacy patterns (backward compatibility)
    legacy_patterns
)

# ============================================================================
# FUTURE PHASES (stubs for planning)
# ============================================================================
# Phase 2: FISCALITE
#   - path('declarations/', ...),
#   - path('tva/', ...),
#   - path('cotisations/', ...),
#
# Phase 3: AUDIT
#   - path('audit/', ...),
#   - path('controles/', ...),
#
# Phase 4+: OTHER MODULES
#   - PAIE
#   - IMMOBILISATIONS
#   - STOCKS
#   - ANALYTIQUE
# ============================================================================
