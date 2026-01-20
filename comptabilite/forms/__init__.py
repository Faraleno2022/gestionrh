"""
Formulaires pour la comptabilité.

Exports principaux:
- Formulaires TVA
- Formulaires de base
"""

from .base import ComptaBaseForm, CompteBancaireForm, DecimalMoneyField
from .tva_forms import (
    RegimeTVAForm,
    TauxTVAForm,
    DeclarationTVAForm,
    LigneDeclarationTVAForm,
    LigneDeclarationTVAFormSet,
    LigneDeclarationTVAInlineFormSet,
    DeclarationTVAFilterForm,
    RegimeTVAFilterForm,
)

# Importer les formulaires depuis forms.py
try:
    from ..forms import (
        PlanComptableForm,
        JournalForm,
        ExerciceForm,
        EcritureForm,
        TiersForm,
        FactureForm,
        ReglementForm,
    )
except ImportError:
    # Si forms.py n'est pas encore complet, on définit des classes vides
    class PlanComptableForm:
        pass
    class JournalForm:
        pass
    class ExerciceForm:
        pass
    class EcritureForm:
        pass
    class TiersForm:
        pass
    class FactureForm:
        pass
    class ReglementForm:
        pass

__all__ = [
    # Base
    'ComptaBaseForm',
    'CompteBancaireForm',
    'DecimalMoneyField',
    # TVA
    'RegimeTVAForm',
    'TauxTVAForm',
    'DeclarationTVAForm',
    'LigneDeclarationTVAForm',
    'LigneDeclarationTVAFormSet',
    'LigneDeclarationTVAInlineFormSet',
    'DeclarationTVAFilterForm',
    'RegimeTVAFilterForm',
    # Comptabilité générale
    'PlanComptableForm',
    'JournalForm',
    'ExerciceForm',
    'EcritureForm',
    'TiersForm',
    'FactureForm',
    'ReglementForm',
]
