"""
Moteur de simulation fiscale multi-barèmes - Guinée
Conformité CGI guinéen: barème RTS progressif + plafond 25% indemnités

Algorithme validé par les tests T01–T17 (cf. _test_rts_tmp.py)
"""
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR
from datetime import date

from .models import TrancheRTS, Constante


# ---------------------------------------------------------------------------
# Helpers d'arrondi (identiques aux tests validés)
# ---------------------------------------------------------------------------

def _half_up(x) -> int:
    """Arrondi ROUND_HALF_UP à l'entier (GNF)."""
    return int(Decimal(str(x)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def _floor_gnf(x) -> int:
    """Arrondi ROUND_FLOOR à l'entier (GNF)."""
    return int(Decimal(str(x)).quantize(Decimal('1'), rounding=ROUND_FLOOR))


# ---------------------------------------------------------------------------
# Barème RTS officiel Guinée – fallback intégré (5 tranches, en vigueur depuis 2019)
# Source : Code général des impôts (CGI) guinéen, art. relatifs à l'IRG/RTS
# Tranches : 0 %, 5 %, 10 %, 15 %, 20 %
# ---------------------------------------------------------------------------

BAREME_CGI_REFERENCE = [
    {'borne_inf': 0,          'borne_sup': 1_000_000,  'taux': Decimal('0')},
    {'borne_inf': 1_000_000,  'borne_sup': 5_000_000,  'taux': Decimal('5')},
    {'borne_inf': 5_000_000,  'borne_sup': 10_000_000, 'taux': Decimal('10')},
    {'borne_inf': 10_000_000, 'borne_sup': 20_000_000, 'taux': Decimal('15')},
    {'borne_inf': 20_000_000, 'borne_sup': None,        'taux': Decimal('20')},
]

# Label affiché pour le fallback
BAREME_CGI_LABEL = 'Barème RTS officiel Guinée 2019+ (0 %/5 %/10 %/15 %/20 %)'
BAREME_FALLBACK_ID = 'fallback'


# ---------------------------------------------------------------------------
# Chargement des données
# ---------------------------------------------------------------------------

def _charger_tranches_db(annee: int, type_bareme: str = 'officiel') -> list:
    """
    Charge les tranches depuis la DB pour une (annee, type_bareme).
    Retourne [] si aucune tranche active trouvée.
    """
    qs = TrancheRTS.objects.filter(
        annee_validite=annee,
        type_bareme=type_bareme,
        actif=True,
    ).order_by('numero_tranche').values('borne_inferieure', 'borne_superieure', 'taux_irg')

    if not qs.exists():
        return []

    result = []
    for t in qs:
        result.append({
            'borne_inf': int(t['borne_inferieure']),
            'borne_sup': int(t['borne_superieure']) if t['borne_superieure'] is not None else None,
            'taux': Decimal(str(t['taux_irg'])),
        })
    return result


def _charger_constantes() -> dict:
    """
    Charge les constantes fiscales actives.
    Complète avec des valeurs par défaut si absentes de la DB.
    """
    constantes = {}
    for c in Constante.objects.filter(actif=True):
        constantes[c.code] = c.valeur

    defaults = {
        'TAUX_CNSS_EMPLOYE':   Decimal('5'),
        'TAUX_CNSS_EMPLOYEUR': Decimal('18'),
        'PLAFOND_CNSS':        Decimal('2500000'),
        'PLANCHER_CNSS':       Decimal('550000'),
        'TAUX_VF':             Decimal('6'),
        'TAUX_TA':             Decimal('2'),
        'TAUX_ONFPP':          Decimal('1.5'),
    }
    for k, v in defaults.items():
        constantes.setdefault(k, v)
    return constantes


def get_baremes_disponibles() -> list:
    """
    Retourne la liste des barèmes utilisables (DB + fallback intégré).
    Chaque entrée : {'id', 'label', 'annee', 'type'}.
    """
    from django.db.models import Count

    options = []
    groupes = (
        TrancheRTS.objects
        .filter(actif=True)
        .values('annee_validite', 'type_bareme')
        .annotate(nb=Count('id'))
        .order_by('-annee_validite', 'type_bareme')
    )

    type_labels = {'officiel': 'Officiel', 'simulation': 'Simulation', 'test': 'Test'}
    for g in groupes:
        annee = g['annee_validite']
        type_b = g['type_bareme']
        bid = f"{annee}-{type_b}"
        options.append({
            'id': bid,
            'label': f'Barème {annee} — {type_labels.get(type_b, type_b)} ({g["nb"]} tranches)',
            'annee': annee,
            'type': type_b,
        })

    # Toujours proposer le barème de référence intégré
    options.append({
        'id': BAREME_FALLBACK_ID,
        'label': BAREME_CGI_LABEL,
        'annee': None,
        'type': 'reference',
    })
    return options


# ---------------------------------------------------------------------------
# Moteur de calcul (un barème)
# ---------------------------------------------------------------------------

def _calcul_rts_par_tranches(base: Decimal, tranches: list) -> tuple:
    """
    Calcul progressif de la RTS par tranches.
    Retourne (total_rts: int, detail_tranches: list).

    Formule: pour chaque tranche [borne_inf, borne_sup) :
        base_tranche = min(base, borne_sup) - borne_inf  (si base > borne_inf)
        impot_tranche = base_tranche * taux / 100  (arrondi HALF_UP)
    """
    if base <= 0:
        return 0, []

    base = Decimal(str(base))
    impot_total = Decimal('0')
    details = []

    for t in tranches:
        borne_inf = Decimal(str(t['borne_inf']))
        taux = Decimal(str(t['taux']))
        borne_sup = Decimal(str(t['borne_sup'])) if t['borne_sup'] is not None else None

        if base <= borne_inf:
            break

        plafond = min(base, borne_sup) if borne_sup is not None else base
        base_tranche = plafond - borne_inf
        impot_tranche = base_tranche * taux / Decimal('100')
        impot_total += impot_tranche

        details.append({
            'borne_inf': int(borne_inf),
            'borne_sup': int(borne_sup) if borne_sup is not None else None,
            'taux': float(taux),
            'base_tranche': _half_up(base_tranche),
            'impot_tranche': _half_up(impot_tranche),
        })

    return _half_up(impot_total), details


def calculer_un_bareme(
    brut: Decimal,
    total_indemnites: Decimal,
    tranches: list,
    constantes: dict,
    nb_salaries: int = 0,
) -> dict:
    """
    Calcule le bulletin complet pour un barème donné.

    Formule CGI Guinée (validée par tests T01–T17):
      CNSS   = half_up(min(brut, plafond_cnss) × taux_cnss_emp / 100)
      plafond_exon = floor(brut × 25%)
      exon   = min(indemnites, plafond_exon)
      depasse = max(0, indemnites − plafond_exon)
      base_rts = brut − CNSS − exon + depasse
      RTS    = calcul progressif (ROUND_HALF_UP sur montants partiels)
      net    = brut − CNSS − RTS
    """
    brut = Decimal(str(brut))
    total_indemnites = Decimal(str(max(Decimal('0'), total_indemnites)))

    plafond_cnss    = constantes.get('PLAFOND_CNSS',        Decimal('2500000'))
    taux_cnss_emp   = constantes.get('TAUX_CNSS_EMPLOYE',   Decimal('5'))
    taux_cnss_pat   = constantes.get('TAUX_CNSS_EMPLOYEUR', Decimal('18'))
    taux_vf         = constantes.get('TAUX_VF',             Decimal('6'))
    taux_ta         = constantes.get('TAUX_TA',             Decimal('2'))
    taux_onfpp      = constantes.get('TAUX_ONFPP',          Decimal('1.5'))

    # -- CNSS employé --
    cnss = _half_up(min(brut, plafond_cnss) * taux_cnss_emp / Decimal('100'))

    # -- CNSS employeur --
    cnss_employeur = _half_up(min(brut, plafond_cnss) * taux_cnss_pat / Decimal('100'))

    # -- Plafond d'exonération indemnités = 25% brut (floor) --
    plafond_exon = _floor_gnf(brut * Decimal('25') / Decimal('100'))
    exon   = int(min(total_indemnites, Decimal(str(plafond_exon))))
    depasse = int(max(Decimal('0'), total_indemnites - Decimal(str(plafond_exon))))

    # -- Base RTS --
    base_rts_raw = int(brut) - cnss - exon + depasse
    base_rts     = max(0, base_rts_raw)

    # -- RTS par tranches --
    rts, detail_tranches = _calcul_rts_par_tranches(Decimal(str(base_rts)), tranches)

    # -- Taux effectif --
    if base_rts > 0:
        taux_effectif = round(rts * 100 / base_rts, 2)
    else:
        taux_effectif = 0.0

    # -- Net --
    net = int(brut) - cnss - rts

    # -- Charges patronales --
    vf    = _half_up(brut * taux_vf / Decimal('100'))
    if nb_salaries < 30:
        ta    = _half_up(brut * taux_ta / Decimal('100'))
        onfpp = 0
    else:
        ta    = 0
        onfpp = _half_up(brut * taux_onfpp / Decimal('100'))

    return {
        'brut':                  int(brut),
        'total_indemnites':      int(total_indemnites),
        'cnss':                  cnss,
        'cnss_employeur':        cnss_employeur,
        'plafond_exon':          plafond_exon,
        'exon':                  exon,
        'depasse':               depasse,
        'base_rts':              base_rts,
        'rts':                   rts,
        'taux_effectif':         taux_effectif,
        'net':                   net,
        'vf':                    vf,
        'ta':                    ta,
        'onfpp':                 onfpp,
        'total_charges_pat':     cnss_employeur + vf + ta + onfpp,
        'detail_tranches':       detail_tranches,
    }


# ---------------------------------------------------------------------------
# Moteur multi-barèmes
# ---------------------------------------------------------------------------

def simuler_multi_baremes(
    brut,
    total_indemnites,
    baremes_ids: list,
    annee_ref: int = None,
    nb_salaries: int = 0,
) -> list:
    """
    Lance la simulation pour plusieurs barèmes et retourne les résultats comparatifs.

    baremes_ids: liste de strings "ANNEE-TYPE" (ex: "2026-officiel") ou "fallback".
    Retourne une liste de dicts enrichis avec bareme_id, bareme_label, etc.
    """
    if annee_ref is None:
        annee_ref = date.today().year

    brut             = Decimal(str(brut))
    total_indemnites = Decimal(str(max(0, total_indemnites)))
    constantes       = _charger_constantes()
    resultats        = []
    type_labels      = {'officiel': 'Officiel', 'simulation': 'Simulation', 'test': 'Test'}

    for bid in baremes_ids:
        if bid == BAREME_FALLBACK_ID:
            tranches = list(BAREME_CGI_REFERENCE)
            label    = BAREME_CGI_LABEL
            annee    = None
            type_b   = 'reference'
        else:
            parts = bid.split('-', 1)
            try:
                annee  = int(parts[0])
                type_b = parts[1] if len(parts) > 1 else 'officiel'
            except (ValueError, IndexError):
                annee  = annee_ref
                type_b = 'officiel'

            tranches = _charger_tranches_db(annee, type_b)
            if not tranches:
                # Fallback : barème intégré si la DB ne contient rien
                tranches = list(BAREME_CGI_REFERENCE)
                label    = f'Barème {annee} {type_b} (fallback référence)'
            else:
                label = f'Barème {annee} — {type_labels.get(type_b, type_b)}'

        result = calculer_un_bareme(
            brut, total_indemnites, tranches, constantes, nb_salaries
        )
        result['bareme_id']      = bid
        result['bareme_label']   = label
        result['annee']          = annee
        result['type_bareme']    = type_b
        result['tranches_bareme'] = [
            {'borne_inf': t['borne_inf'], 'borne_sup': t['borne_sup'], 'taux': float(t['taux'])}
            for t in tranches
        ]
        resultats.append(result)

    return resultats
