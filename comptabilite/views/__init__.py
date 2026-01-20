"""
Views pour le module comptabilité.
Ce fichier importe et expose toutes les vues des sous-modules.
"""

# Importer les vues de rapprochements
from .rapprochements.views import (
    CompteBancaireListView,
    CompteBancaireDetailView,
    CompteBancaireCreateView,
    CompteBancaireUpdateView,
    CompteBancaireDeleteView,
    RapprochementListView,
    RapprochementDetailView,
    RapprochementCreateView,
    RapprochementUpdateView,
    RapprochementDeleteView,
    OperationImportView,
    LettrageView,
    LettrageAnnulationView,
    RapprochementFinalisationView,
)

# Importer les vues de fiscalité
try:
    from .fiscalite.tva_views import (
        RegimeTVAListView,
        RegimeTVACreateView,
        RegimeTVAUpdateView,
        RegimeTVADeleteView,
        TauxTVAListView,
        TauxTVACreateView,
        TauxTVAUpdateView,
        TauxTVADeleteView,
        DeclarationTVAListView,
        DeclarationTVACreateView,
        DeclarationTVAUpdateView,
        DeclarationTVADeleteView,
        LigneDeclarationTVAView,
        LigneDeclarationTVACreateView,
        LigneDeclarationTVAUpdateView,
        LigneDeclarationTVADeleteView,
    )
except ImportError:
    # Si les vues de fiscalité ne sont pas encore implémentées
    pass

# Importer les vues d'audit
try:
    from .audit.views import (
        AuditListView,
        AuditDetailView,
        AuditCreateView,
        AuditUpdateView,
        AuditDeleteView,
    )
except ImportError:
    # Si les vues d'audit ne sont pas encore implémentées
    pass

# Importer les vues de base
try:
    from .base.views import (
        DashboardView,
        PlanComptableListView,
        PlanComptableCreateView,
        PlanComptableUpdateView,
        PlanComptableDeleteView,
        JournalListView,
        JournalCreateView,
        JournalUpdateView,
        JournalDeleteView,
        EcritureListView,
        EcritureCreateView,
        EcritureUpdateView,
        EcritureDeleteView,
    )
except ImportError:
    # Si les vues de base ne sont pas encore implémentées
    pass

# Importer les vues legacy depuis views.py principal
from ..views import (
    plan_comptable_list, plan_comptable_create, plan_comptable_detail, plan_comptable_update,
    journal_list, journal_create, journal_update, journal_delete,
    ecriture_list, ecriture_create, ecriture_detail, ecriture_update, ecriture_delete,
    tiers_list, tiers_create, tiers_detail, tiers_update, tiers_delete,
    facture_list, facture_create, facture_detail, facture_update, facture_delete,
    reglement_list, reglement_create, reglement_detail, reglement_update, reglement_delete,
)

__all__ = [
    # Rapprochements
    'CompteBancaireListView',
    'CompteBancaireDetailView',
    'CompteBancaireCreateView',
    'CompteBancaireUpdateView',
    'CompteBancaireDeleteView',
    'RapprochementListView',
    'RapprochementDetailView',
    'RapprochementCreateView',
    'RapprochementUpdateView',
    'RapprochementDeleteView',
    'OperationImportView',
    'LettrageView',
    'LettrageAnnulationView',
    'RapprochementFinalisationView',
    # Vues legacy
    'plan_comptable_list', 'plan_comptable_create', 'plan_comptable_detail', 'plan_comptable_update',
    'journal_list', 'journal_create', 'journal_update', 'journal_delete',
    'ecriture_list', 'ecriture_create', 'ecriture_detail', 'ecriture_update', 'ecriture_delete',
    'tiers_list', 'tiers_create', 'tiers_detail', 'tiers_update', 'tiers_delete',
    'facture_list', 'facture_create', 'facture_detail', 'facture_update', 'facture_delete',
    'reglement_list', 'reglement_create', 'reglement_detail', 'reglement_update', 'reglement_delete',
]
