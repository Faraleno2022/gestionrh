"""
Moteur d'évaluation de formules de paie — sécurisé (sans exec/import).

Variables disponibles dans les formules :
  brut, cnss, indemnites, salaire_base, primes, heures_sup,
  anciennete_mois, anciennete_ans, nb_enfants, nb_conjoints, plafond_cnss
"""
import math
from decimal import Decimal

VARIABLES_AUTORISEES = {
    'brut', 'cnss', 'indemnites', 'salaire_base', 'primes',
    'heures_sup', 'anciennete_mois', 'anciennete_ans',
    'nb_enfants', 'nb_conjoints', 'plafond_cnss',
}

FONCTIONS_AUTORISEES = {
    'min': min,
    'max': max,
    'abs': abs,
    'round': round,
    'int': int,
    'float': float,
}

# Mots interdits dans les formules (protection injection)
MOTS_INTERDITS = [
    'import', 'exec', 'eval', 'open', 'file', '__',
    'os', 'sys', 'subprocess', 'builtins', 'globals',
    'locals', 'vars', 'dir', 'getattr', 'setattr',
    'delattr', 'hasattr', 'compile', 'input', 'print',
]


def evaluer_formule(formule: str, variables: dict) -> Decimal:
    """
    Évalue une formule de paie de manière sécurisée.

    Retourne le résultat en Decimal (>= 0), ou lève ValueError si erreur.

    :param formule: Expression Python simple (ex: ``brut * 0.25``)
    :param variables: Dictionnaire des valeurs (clés = noms de variables)
    :raises ValueError: Si la formule est vide, contient des mots interdits ou est invalide
    """
    if not formule or not formule.strip():
        raise ValueError("Formule vide")

    formule_lower = formule.lower()
    for mot in MOTS_INTERDITS:
        if mot in formule_lower:
            raise ValueError(f"Mot interdit dans la formule : '{mot}'")

    # Construire le namespace d'évaluation
    namespace = dict(FONCTIONS_AUTORISEES)
    for var in VARIABLES_AUTORISEES:
        namespace[var] = float(variables.get(var, 0))

    try:
        resultat = eval(formule, {"__builtins__": {}}, namespace)  # noqa: S307
        return Decimal(str(max(0.0, float(resultat))))
    except ZeroDivisionError:
        return Decimal('0')
    except Exception as exc:
        raise ValueError(f"Erreur dans la formule '{formule}' : {exc}") from exc


EXEMPLES_FORMULES = {
    'exoneration': [
        ('Plafond 25% du brut (CGI strict)', 'min(indemnites, brut * 0.25)'),
        ('Plafond 30% du brut', 'min(indemnites, brut * 0.30)'),
        ('Exonération conditionnelle 25%', 'indemnites if indemnites <= brut * 0.25 else brut * 0.25'),
        ('Exonération intégrale', 'indemnites'),
    ],
    'base_vf': [
        ('Brut direct (simplifié)', 'brut'),
        ('Brut moins abattement fixe', 'brut - 150000 if brut >= 2500000 else brut'),
        ('94% du brut', 'brut * 0.94'),
        ('Brut moins CNSS', 'brut - cnss'),
    ],
    'base_rts': [
        ('Formule standard (brut - CNSS - exo 25%)', 'brut - cnss - min(indemnites, brut * 0.25)'),
        ('Avec plafond 30%', 'brut - cnss - min(indemnites, brut * 0.30)'),
        ('Base simplifiée (brut - CNSS)', 'brut - cnss'),
        ('Base avec abattement 10%', '(brut - cnss) * 0.90'),
    ],
}


def valider_formule(formule: str) -> dict:
    """
    Valide une formule de paie sans l'évaluer définitivement.

    Retourne un dictionnaire avec:
      - ``valide`` (bool)
      - ``erreurs`` (list[str]) : blocages empêchant l'utilisation
      - ``avertissements`` (list[str]) : points d'attention non bloquants
      - ``resultat_test`` (Decimal|None) : résultat sur valeurs-test si valide
    """
    erreurs = []
    avertissements = []
    resultat_test = None

    if not formule or not formule.strip():
        erreurs.append("La formule est vide.")
        return {'valide': False, 'erreurs': erreurs, 'avertissements': avertissements, 'resultat_test': None}

    formule_lower = formule.lower()

    # Vérification mots interdits
    for mot in MOTS_INTERDITS:
        if mot in formule_lower:
            erreurs.append(f"Mot interdit détecté : '{mot}'")

    if erreurs:
        return {'valide': False, 'erreurs': erreurs, 'avertissements': avertissements, 'resultat_test': None}

    # Détection division par zéro potentielle
    import re
    if re.search(r'/\s*(0(?:[^.]|$)|\bbrut\b|\bsalaire_base\b)', formule_lower):
        avertissements.append(
            "Division potentielle par zéro détectée : vérifiez les diviseurs (ex. brut, salaire_base) "
            "car ils peuvent valoir 0."
        )

    # Test avec valeurs d'exemple
    test = tester_formule(formule)
    if not test.get('succes'):
        erreurs.append(test.get('erreur', 'Erreur d\'évaluation inconnue'))
        return {'valide': False, 'erreurs': erreurs, 'avertissements': avertissements, 'resultat_test': None}

    resultat_test = test['resultat']

    # Vérification résultat positif (tester_formule retourne déjà max(0, …) mais on logue l'avert.)
    if float(resultat_test) < 0:
        avertissements.append("Le résultat calculé est négatif (sera ramené à 0).")

    # Vérification plage réaliste (0 à 100 000 000 GNF)
    PLAFOND_MAX = 100_000_000
    if float(resultat_test) > PLAFOND_MAX:
        avertissements.append(
            f"Le résultat ({float(resultat_test):,.0f} GNF) dépasse le plafond "
            f"réaliste de {PLAFOND_MAX:,.0f} GNF. Vérifiez la formule."
        )

    return {
        'valide': True,
        'erreurs': erreurs,
        'avertissements': avertissements,
        'resultat_test': resultat_test,
    }


def tester_formule(formule: str) -> dict:
    """
    Teste une formule avec des valeurs d'exemple.

    :param formule: Expression à tester
    :return: Dict avec clés ``succes`` (bool), ``resultat`` ou ``erreur``,
             et ``variables_test``
    """
    variables_test = {
        'brut': 3_000_000,
        'cnss': 125_000,
        'indemnites': 700_000,
        'salaire_base': 2_000_000,
        'primes': 300_000,
        'heures_sup': 150_000,
        'anciennete_mois': 24,
        'anciennete_ans': 2,
        'nb_enfants': 2,
        'nb_conjoints': 1,
        'plafond_cnss': 2_500_000,
    }
    try:
        resultat = evaluer_formule(formule, variables_test)
        return {
            'succes': True,
            'resultat': resultat,
            'variables_test': variables_test,
        }
    except ValueError as exc:
        return {
            'succes': False,
            'erreur': str(exc),
        }
