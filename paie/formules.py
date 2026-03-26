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
