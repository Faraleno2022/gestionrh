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

from django.urls import path, include
import sys
import os
# Ajouter le chemin du module pour importer views.py directement
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import views as comptabilite_views_legacy
# Importer les classes depuis les sous-modules
from views.rapprochements.views import (
    CompteBancaireListView, CompteBancaireDetailView, CompteBancaireCreateView, CompteBancaireUpdateView, CompteBancaireDeleteView,
    RapprochementListView, RapprochementDetailView, RapprochementCreateView, RapprochementUpdateView, RapprochementDeleteView,
    OperationImportView,
    LettrageView, LettrageAnnulationView, RapprochementFinalisationView,
)

app_name = 'comptabilite'

# ============================================================================
# RAPPROCHEMENTS BANCAIRES - Main Module for Phase 1
# ============================================================================

# Compte Bancaire URLs
compte_bancaire_patterns = [
    path('comptes/', CompteBancaireListView.as_view(), name='compte-bancaire-list'),
    path('comptes/nouveau/', CompteBancaireCreateView.as_view(), name='compte-bancaire-create'),
    path('comptes/<uuid:pk>/', CompteBancaireDetailView.as_view(), name='compte-bancaire-detail'),
    path('comptes/<uuid:pk>/editer/', CompteBancaireUpdateView.as_view(), name='compte-bancaire-update'),
    path('comptes/<uuid:pk>/supprimer/', CompteBancaireDeleteView.as_view(), name='compte-bancaire-delete'),
]

# Rapprochement Bancaire URLs
rapprochement_patterns = [
    path('rapprochements/', RapprochementListView.as_view(), name='rapprochement-list'),
    path('rapprochements/nouveau/', RapprochementCreateView.as_view(), name='rapprochement-create'),
    path('rapprochements/<uuid:pk>/', RapprochementDetailView.as_view(), name='rapprochement-detail'),
    path('rapprochements/<uuid:pk>/editer/', RapprochementUpdateView.as_view(), name='rapprochement-update'),
    path('rapprochements/<uuid:pk>/supprimer/', RapprochementDeleteView.as_view(), name='rapprochement-delete'),
    path('rapprochements/<uuid:pk>/finaliser/', RapprochementFinalisationView.as_view(), name='rapprochement-finalize'),
]

# Lettrage (Matching) URLs
lettrage_patterns = [
    path('rapprochements/<uuid:rapprochement_id>/lettrer/', LettrageView.as_view(), name='rapprochement-lettrage'),
    path('rapprochements/<uuid:rapprochement_id>/lettrage/<uuid:lettrage_id>/supprimer/', LettrageAnnulationView.as_view(), name='rapprochement-lettrage-delete'),
]

# ============================================================================
# IMPORT/EXPORT Operations
# ============================================================================

import_export_patterns = [
    # Import
    path('importer/', OperationImportView.as_view(), name='operation-import'),
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
]

# ============================================================================
# LEGACY/EXISTING URLs (Keep for backward compatibility)
# ============================================================================

legacy_patterns = [
    # Plan comptable
    path('plan-comptable/', comptabilite_views_legacy.plan_comptable_list, name='plan_comptable_list'),
    path('plan-comptable/ajouter/', comptabilite_views_legacy.plan_comptable_create, name='plan_comptable_create'),
    path('plan-comptable/<int:pk>/', comptabilite_views_legacy.plan_comptable_detail, name='plan_comptable_detail'),
    path('plan-comptable/<int:pk>/modifier/', comptabilite_views_legacy.plan_comptable_update, name='plan_comptable_update'),
    
    # Journaux
    path('journaux/', comptabilite_views_legacy.journal_list, name='journal_list'),
    path('journaux/ajouter/', comptabilite_views_legacy.journal_create, name='journal_create'),
    path('journaux/<int:pk>/modifier/', comptabilite_views_legacy.journal_update, name='journal_update'),
    path('journaux/<int:pk>/supprimer/', comptabilite_views_legacy.journal_delete, name='journal_delete'),
    
    # Écritures comptables
    path('ecritures/', comptabilite_views_legacy.ecriture_list, name='ecriture_list'),
    path('ecritures/ajouter/', comptabilite_views_legacy.ecriture_create, name='ecriture_create'),
    path('ecritures/<int:pk>/', comptabilite_views_legacy.ecriture_detail, name='ecriture_detail'),
    path('ecritures/<int:pk>/modifier/', comptabilite_views_legacy.ecriture_update, name='ecriture_update'),
    path('ecritures/<int:pk>/supprimer/', comptabilite_views_legacy.ecriture_delete, name='ecriture_delete'),
    
    # Tiers
    path('tiers/', comptabilite_views_legacy.tiers_list, name='tiers_list'),
    path('tiers/ajouter/', comptabilite_views_legacy.tiers_create, name='tiers_create'),
    path('tiers/<int:pk>/', comptabilite_views_legacy.tiers_detail, name='tiers_detail'),
    path('tiers/<int:pk>/modifier/', comptabilite_views_legacy.tiers_update, name='tiers_update'),
    path('tiers/<int:pk>/supprimer/', comptabilite_views_legacy.tiers_delete, name='tiers_delete'),
    
    # Factures
    path('factures/', comptabilite_views_legacy.facture_list, name='facture_list'),
    path('factures/ajouter/', comptabilite_views_legacy.facture_create, name='facture_create'),
    path('factures/<int:pk>/', comptabilite_views_legacy.facture_detail, name='facture_detail'),
    path('factures/<int:pk>/modifier/', comptabilite_views_legacy.facture_update, name='facture_update'),
    path('factures/<int:pk>/supprimer/', comptabilite_views_legacy.facture_delete, name='facture_delete'),
    
    # Règlements
    path('reglements/', comptabilite_views_legacy.reglement_list, name='reglement_list'),
    path('reglements/ajouter/', comptabilite_views_legacy.reglement_create, name='reglement_create'),
    path('reglements/<int:pk>/', comptabilite_views_legacy.reglement_detail, name='reglement_detail'),
    path('reglements/<int:pk>/modifier/', comptabilite_views_legacy.reglement_update, name='reglement_update'),
    path('reglements/<int:pk>/supprimer/', comptabilite_views_legacy.reglement_delete, name='reglement_delete'),
    
    # États financiers
    path('etats/grand-livre/', comptabilite_views_legacy.grand_livre, name='grand_livre'),
    path('etats/grand-livre/pdf/', comptabilite_views_legacy.grand_livre_pdf, name='grand_livre_pdf'),
    path('etats/grand-livre/excel/', comptabilite_views_legacy.grand_livre_excel, name='grand_livre_excel'),
    path('etats/balance/', comptabilite_views_legacy.balance, name='balance'),
    path('etats/balance/pdf/', comptabilite_views_legacy.balance_pdf, name='balance_pdf'),
    path('etats/balance/excel/', comptabilite_views_legacy.balance_excel, name='balance_excel'),
    path('etats/journal-general/', comptabilite_views_legacy.journal_general, name='journal_general'),
    path('etats/journal-general/pdf/', comptabilite_views_legacy.journal_general_pdf, name='journal_general_pdf'),
    path('etats/journal-general/excel/', comptabilite_views_legacy.journal_general_excel, name='journal_general_excel'),
    path('etats/bilan/', comptabilite_views_legacy.bilan, name='bilan'),
    path('etats/bilan/pdf/', comptabilite_views_legacy.bilan_pdf, name='bilan_pdf'),
    path('etats/bilan/excel/', comptabilite_views_legacy.bilan_excel, name='bilan_excel'),
    path('etats/compte-resultat/', comptabilite_views_legacy.compte_resultat, name='compte_resultat'),
    path('etats/compte-resultat/pdf/', comptabilite_views_legacy.compte_resultat_pdf, name='compte_resultat_pdf'),
    path('etats/compte-resultat/excel/', comptabilite_views_legacy.compte_resultat_excel, name='compte_resultat_excel'),
    
    # Clients & Fournisseurs détaillés
    path('clients/', comptabilite_views_legacy.compte_client_list, name='compte_client_list'),
    path('clients/<uuid:pk>/', comptabilite_views_legacy.compte_client_detail, name='compte_client_detail'),
    path('clients/vieillissement/', comptabilite_views_legacy.vieillissement_creances, name='vieillissement_creances'),
    path('clients/impayes/', comptabilite_views_legacy.impayes_clients, name='impayes_clients'),
    path('fournisseurs/', comptabilite_views_legacy.compte_fournisseur_list, name='compte_fournisseur_list'),
    path('fournisseurs/<uuid:pk>/', comptabilite_views_legacy.compte_fournisseur_detail, name='compte_fournisseur_detail'),
    path('fournisseurs/vieillissement/', comptabilite_views_legacy.vieillissement_dettes, name='vieillissement_dettes'),
    path('fournisseurs/impayes/', comptabilite_views_legacy.impayes_fournisseurs, name='impayes_fournisseurs'),
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
