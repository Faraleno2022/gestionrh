"""
Service de rétro-calcul salarial : Net → Brut
=============================================
Permet de déterminer le salaire BRUT à saisir pour qu'un employé
reçoive exactement le NET négocié/convenu (ex: 5 500 000 GNF net).

Algorithme : Dichotomie (binary search) sur la fonction brut→net
Conformité  : Législation guinéenne (CNSS + RTS barème CGI officiel)

Utilisation :
    from paie.services_retropaie import retropaie_net_vers_brut
    resultat = retropaie_net_vers_brut(net_cible=5_500_000, annee=2025)
"""
from decimal import Decimal, ROUND_HALF_UP
from datetime import date


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _d(valeur):
    """Convertit en Decimal propre."""
    return Decimal(str(valeur))


def _arrondir(montant):
    """Arrondit à l'unité (pas de centimes en GNF)."""
    return _d(montant).quantize(Decimal('1'), rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# Calcul CNSS employé
# ---------------------------------------------------------------------------

def _calculer_cnss(brut, plancher, plafond, taux_employe):
    """
    Calcule la cotisation CNSS salarié selon les règles guinéennes.

    Règles :
    - Brut < 10 % du plancher  → pas de cotisation
    - Brut < plancher          → cotiser sur le plancher
    - Plancher ≤ brut ≤ plafond → cotiser sur le brut réel
    - Brut > plafond           → cotiser sur le plafond

    Retourne (cnss_employe, base_cnss_plafonnee).
    """
    seuil_min = _arrondir(plancher * Decimal('0.10'))   # 10 % du plancher
    if brut < seuil_min:
        return Decimal('0'), Decimal('0')

    base = _arrondir(max(min(brut, plafond), plancher))
    cnss = _arrondir(base * taux_employe / Decimal('100'))
    return cnss, base


# ---------------------------------------------------------------------------
# Calcul RTS/IRG progressif
# ---------------------------------------------------------------------------

def _calculer_rts(base_imposable, tranches):
    """
    Calcule l'IRG/RTS selon le barème progressif à tranches.

    tranches : liste de dict {borne_inferieure, borne_superieure, taux_irg}
               ou objets TrancheRTS (accès par attributs).
    """
    if base_imposable <= 0:
        return Decimal('0')

    # Normaliser les tranches en tuples (borne_inf, borne_sup, taux)
    seuils = []
    for i, t in enumerate(tranches):
        if isinstance(t, dict):
            bi  = _d(t['borne_inferieure'])
            bs  = _d(t['borne_superieure']) if t.get('borne_superieure') is not None else None
            tx  = _d(t['taux_irg'])
        else:
            bi  = _d(t.borne_inferieure)
            bs  = _d(t.borne_superieure) if t.borne_superieure is not None else None
            tx  = _d(t.taux_irg)

        # Combler les gaps d'1 GNF entre tranches (1 000 001 → 1 000 000)
        if i > 0 and seuils:
            prev_sup = seuils[-1][1]
            if prev_sup is not None and bi > prev_sup and bi <= prev_sup + 2:
                bi = prev_sup

        seuils.append((bi, bs, tx))

    irg = Decimal('0')
    for bi, bs, tx in seuils:
        if base_imposable <= bi:
            break
        montant = (min(base_imposable, bs) - bi) if bs is not None else (base_imposable - bi)
        if montant > 0:
            irg += _arrondir(montant * tx / Decimal('100'))

    return irg


# ---------------------------------------------------------------------------
# Calcul NET depuis BRUT (sens direct)
# ---------------------------------------------------------------------------

def _net_depuis_brut(brut, constantes, tranches, pct_indem_exonerees=Decimal('0')):
    """
    Calcule le net depuis un brut donné.

    pct_indem_exonerees : pourcentage du brut représenté par des indemnités
                          forfaitaires exonérées de RTS (0 à 25, ex: 15 pour 15 %).
    Retourne (net, cnss, base_cnss, base_rts, rts).
    """
    plancher  = constantes.get('PLANCHER_CNSS',     Decimal('550000'))
    plafond   = constantes.get('PLAFOND_CNSS',      Decimal('2500000'))
    taux_cnss = constantes.get('TAUX_CNSS_EMPLOYE', Decimal('5'))

    cnss, base_cnss = _calculer_cnss(brut, plancher, plafond, taux_cnss)

    # Exonération indemnités forfaitaires (CGI Guinée : max 25 % du brut)
    exo = _arrondir(brut * min(pct_indem_exonerees, Decimal('25')) / Decimal('100'))

    base_rts = max(brut - cnss - exo, Decimal('0'))
    rts      = _calculer_rts(base_rts, tranches)
    net      = _arrondir(brut - cnss - rts)

    return net, cnss, base_cnss, base_rts, rts


# ---------------------------------------------------------------------------
# Service principal : Net → Brut (dichotomie)
# ---------------------------------------------------------------------------

def retropaie_net_vers_brut(
    net_cible,
    annee=None,
    pct_indemnites_forfaitaires=0,
    garantir_net_minimum=True,
    max_iterations=120,
    tolerance=1,
):
    """
    Calcule le salaire BRUT nécessaire pour obtenir exactement le NET convenu.

    Paramètres
    ----------
    net_cible : int | float | Decimal
        Net mensuel souhaité en GNF (ex: 5_500_000).
    annee : int, optionnel
        Année du barème RTS à utiliser (défaut : année courante).
    pct_indemnites_forfaitaires : int | float
        Pourcentage du brut constitué d'indemnités forfaitaires exonérées de RTS
        (ex: 15 si transport + logement = 15 % du brut). Max effectif = 25 %.
    garantir_net_minimum : bool
        Si True, arrondit légèrement le brut vers le haut pour s'assurer que
        l'employé reçoit AU MOINS le net négocié (recommandé).
    max_iterations : int
        Nombre maximum d'itérations de dichotomie (120 suffit largement).
    tolerance : int
        Écart maximal acceptable en GNF entre net_calculé et net_cible (défaut : 1 GNF).

    Retourne
    --------
    dict avec les clés :
        brut           – Brut à saisir dans l'application
        cnss           – CNSS employé déduit
        base_cnss      – Base plafonnée de la CNSS
        base_rts       – Base imposable à l'IRG/RTS
        rts            – Montant RTS déduit
        net_calcule    – Net effectif avec ce brut (≥ net_cible si garantir_net_minimum)
        net_cible      – Net demandé
        ecart          – net_calcule − net_cible (0 ou 1 GNF max)
        ok             – True si convergence réussie
        iterations     – Nombre d'itérations utilisées
        detail_tranches – Détail par tranche RTS (liste)
    """
    from .cache_service import PayrollCacheService

    net_cible = _arrondir(_d(net_cible))
    pct_indem = _d(pct_indemnites_forfaitaires)

    if annee is None:
        annee = date.today().year

    # ---- Chargement des paramètres de paie --------------------------------
    constantes = PayrollCacheService.get_constantes(date_reference=date(annee, 1, 1))
    tranches   = PayrollCacheService.get_tranches_rts(annee)

    # Valeurs par défaut si base vide
    constantes.setdefault('PLANCHER_CNSS',     Decimal('550000'))
    constantes.setdefault('PLAFOND_CNSS',      Decimal('2500000'))
    constantes.setdefault('TAUX_CNSS_EMPLOYE', Decimal('5'))

    # ---- Dichotomie -------------------------------------------------------
    low  = net_cible                      # Brut minimum possible = net cible
    high = _arrondir(net_cible * Decimal('2'))   # Borne haute (généreux)

    brut_opt  = high
    iterations = 0

    for _ in range(max_iterations):
        iterations += 1
        mid = _arrondir((low + high) / 2)

        net_mid, *_ = _net_depuis_brut(mid, constantes, tranches, pct_indem)

        if abs(net_mid - net_cible) <= _d(tolerance):
            brut_opt = mid
            break

        if net_mid < net_cible:
            low = mid
        else:
            high = mid

        brut_opt = mid

    # ---- Garantie du net minimum OU affinement net exact ------------------
    if garantir_net_minimum:
        # Mode net_minimum : s'assurer que net >= net_cible
        net_test, *_ = _net_depuis_brut(brut_opt, constantes, tranches, pct_indem)
        while net_test < net_cible:
            brut_opt += Decimal('1000')
            net_test, *_ = _net_depuis_brut(brut_opt, constantes, tranches, pct_indem)
        mode = 'net_minimum'
    else:
        # Mode net_exact : trouver le brut qui donne le net le plus proche (≤ net_cible + 1 GNF)
        # Étape 1 : affiner par pas de 100 GNF vers le bas depuis brut_opt
        net_test, *_ = _net_depuis_brut(brut_opt, constantes, tranches, pct_indem)
        # D'abord descendre si net_test > net_cible
        while brut_opt > net_cible:
            brut_candidat = brut_opt - Decimal('100')
            net_candidat, *_ = _net_depuis_brut(brut_candidat, constantes, tranches, pct_indem)
            if net_candidat < net_cible:
                break
            brut_opt = brut_candidat
            net_test = net_candidat
        # Étape 2 : affiner par pas de 1 GNF
        net_test, *_ = _net_depuis_brut(brut_opt, constantes, tranches, pct_indem)
        if net_test > net_cible:
            # Descendre d'1 GNF à la fois jusqu'à passer sous net_cible
            while brut_opt > net_cible:
                brut_candidat = brut_opt - Decimal('1')
                net_candidat, *_ = _net_depuis_brut(brut_candidat, constantes, tranches, pct_indem)
                if net_candidat < net_cible:
                    # Choisir le brut qui minimise l'écart absolu
                    ecart_actuel = abs(net_test - net_cible)
                    ecart_candidat = abs(net_candidat - net_cible)
                    if ecart_candidat < ecart_actuel:
                        brut_opt = brut_candidat
                        net_test = net_candidat
                    break
                brut_opt = brut_candidat
                net_test = net_candidat
        else:
            # net_test < net_cible : monter d'1 GNF jusqu'au plus proche
            while True:
                brut_candidat = brut_opt + Decimal('1')
                net_candidat, *_ = _net_depuis_brut(brut_candidat, constantes, tranches, pct_indem)
                if net_candidat > net_cible:
                    # Comparer les deux côtés et prendre le plus proche
                    ecart_actuel = net_cible - net_test
                    ecart_candidat = net_candidat - net_cible
                    if ecart_candidat < ecart_actuel:
                        brut_opt = brut_candidat
                    break
                brut_opt = brut_candidat
                net_test = net_candidat
        mode = 'net_exact'

    # ---- Résultat final ---------------------------------------------------
    net_final, cnss_f, base_cnss_f, base_rts_f, rts_f = _net_depuis_brut(
        brut_opt, constantes, tranches, pct_indem
    )

    # Détail par tranche RTS
    detail_tranches = _detail_tranches(base_rts_f, tranches)

    return {
        'brut':            brut_opt,
        'cnss':            cnss_f,
        'base_cnss':       base_cnss_f,
        'base_rts':        base_rts_f,
        'rts':             rts_f,
        'net_calcule':     net_final,
        'net_cible':       net_cible,
        'ecart':           net_final - net_cible,
        'ok':              abs(net_final - net_cible) <= _d(tolerance) * 10,
        'iterations':      iterations,
        'detail_tranches': detail_tranches,
        'mode':            mode,
    }


# ---------------------------------------------------------------------------
# Détail par tranche (pour affichage pédagogique)
# ---------------------------------------------------------------------------

def calculer_charges_patronales(brut, annee=None, nb_salaries=0):
    """
    Calcule les charges patronales pour un brut donné.

    Retourne dict :
        cnss_employeur, vf, ta, libelle_ta, total, cout_total_employeur
    """
    from .cache_service import PayrollCacheService

    if annee is None:
        annee = date.today().year

    constantes = PayrollCacheService.get_constantes(date_reference=date(annee, 1, 1))
    constantes.setdefault('PLANCHER_CNSS',       Decimal('550000'))
    constantes.setdefault('PLAFOND_CNSS',        Decimal('2500000'))
    constantes.setdefault('TAUX_CNSS_EMPLOYEUR', Decimal('18'))
    constantes.setdefault('TAUX_VF',             Decimal('6'))
    constantes.setdefault('TAUX_TA',             Decimal('2'))
    constantes.setdefault('TAUX_ONFPP',          Decimal('1.5'))

    brut = _arrondir(_d(brut))
    plancher     = constantes['PLANCHER_CNSS']
    plafond      = constantes['PLAFOND_CNSS']
    taux_cnss_pat = constantes['TAUX_CNSS_EMPLOYEUR']
    taux_vf       = constantes['TAUX_VF']
    libelle_ta    = 'ONFPP' if nb_salaries >= 25 else 'TA'
    taux_ta       = constantes['TAUX_ONFPP'] if nb_salaries >= 25 else constantes['TAUX_TA']

    seuil = _arrondir(plancher * Decimal('0.10'))
    if brut < seuil:
        cnss_pat = Decimal('0')
    else:
        base = _arrondir(max(min(brut, plafond), plancher))
        cnss_pat = _arrondir(base * taux_cnss_pat / Decimal('100'))

    vf = _arrondir(brut * taux_vf  / Decimal('100'))
    ta = _arrondir(brut * taux_ta  / Decimal('100'))
    total = cnss_pat + vf + ta

    return {
        'cnss_employeur':      int(cnss_pat),
        'vf':                  int(vf),
        'ta':                  int(ta),
        'libelle_ta':          libelle_ta,
        'total':               int(total),
        'cout_total_employeur': int(brut) + int(total),
    }


def cout_total_vers_brut(
    cout_total,
    annee=None,
    pct_indemnites_forfaitaires=0,
    nb_salaries=0,
    max_iterations=120,
):
    """
    Calcule le brut et le net depuis un coût total employeur (budget tout compris).

    cout_total = brut + CNSS_employeur + VF + TA (ou ONFPP)

    Paramètres
    ----------
    cout_total : montant total que l'entreprise paie pour l'employé
    nb_salaries : nombre de salariés (>= 25 → ONFPP 1.5%, sinon TA 2%)

    Retourne
    --------
    dict : brut, net, cnss_employe, rts, charges_patronales (détail), cout_total_reel
    """
    from .cache_service import PayrollCacheService

    cout_total = _arrondir(_d(cout_total))
    pct_indem = _d(pct_indemnites_forfaitaires)

    if annee is None:
        annee = date.today().year

    constantes = PayrollCacheService.get_constantes(date_reference=date(annee, 1, 1))
    tranches = PayrollCacheService.get_tranches_rts(annee)

    constantes.setdefault('PLANCHER_CNSS',     Decimal('550000'))
    constantes.setdefault('PLAFOND_CNSS',      Decimal('2500000'))
    constantes.setdefault('TAUX_CNSS_EMPLOYE', Decimal('5'))
    constantes.setdefault('TAUX_CNSS_EMPLOYEUR', Decimal('18'))
    constantes.setdefault('TAUX_VF',           Decimal('6'))
    constantes.setdefault('TAUX_TA',           Decimal('2'))
    constantes.setdefault('TAUX_ONFPP',        Decimal('1.5'))

    plancher     = constantes['PLANCHER_CNSS']
    plafond      = constantes['PLAFOND_CNSS']
    taux_cnss_pat = constantes['TAUX_CNSS_EMPLOYEUR']
    taux_vf       = constantes['TAUX_VF']
    taux_ta_onfpp = constantes['TAUX_ONFPP'] if nb_salaries >= 25 else constantes['TAUX_TA']
    libelle_ta    = 'ONFPP' if nb_salaries >= 25 else 'TA'

    def _charges_pat(brut):
        seuil = _arrondir(plancher * Decimal('0.10'))
        if brut < seuil:
            cnss_pat = Decimal('0')
        else:
            base = _arrondir(max(min(brut, plafond), plancher))
            cnss_pat = _arrondir(base * taux_cnss_pat / Decimal('100'))
        vf = _arrondir(brut * taux_vf / Decimal('100'))
        ta = _arrondir(brut * taux_ta_onfpp / Decimal('100'))
        return cnss_pat, vf, ta

    def _cout(brut):
        c, v, t = _charges_pat(brut)
        return brut + c + v + t

    # Dichotomie : trouver brut tel que _cout(brut) ≈ cout_total
    low  = Decimal('0')
    high = cout_total  # brut ne peut dépasser le budget total
    brut_opt = _arrondir(cout_total / Decimal('1.26'))  # estimation init

    for _ in range(max_iterations):
        mid = _arrondir((low + high) / 2)
        if abs(_cout(mid) - cout_total) <= _d('1'):
            brut_opt = mid
            break
        if _cout(mid) < cout_total:
            low = mid
        else:
            high = mid
        brut_opt = mid

    # Garantir que le coût calculé ne dépasse pas le budget
    while _cout(brut_opt) > cout_total:
        brut_opt -= Decimal('1')

    # Résultats complets
    cnss_pat, vf, ta = _charges_pat(brut_opt)
    total_pat = cnss_pat + vf + ta
    net, cnss_emp, base_cnss, base_rts, rts = _net_depuis_brut(
        brut_opt, constantes, tranches, pct_indem
    )
    detail_t = _detail_tranches(base_rts, tranches)

    return {
        'cout_total_vise':  int(cout_total),
        'cout_total_reel':  int(_cout(brut_opt)),
        'brut':             brut_opt,
        'cnss_employe':     cnss_emp,
        'base_cnss':        base_cnss,
        'base_rts':         base_rts,
        'rts':              rts,
        'net':              net,
        'charges_patronales': {
            'cnss_employeur': int(cnss_pat),
            'vf':             int(vf),
            'ta':             int(ta),
            'libelle_ta':     libelle_ta,
            'total':          int(total_pat),
        },
        'detail_tranches':  detail_t,
        'ok': abs(int(_cout(brut_opt)) - int(cout_total)) <= 1000,
        'annee':            annee,
    }


def _detail_tranches(base_imposable, tranches):
    """Retourne le détail du calcul RTS tranche par tranche."""
    if base_imposable <= 0:
        return []

    seuils = []
    for i, t in enumerate(tranches):
        if isinstance(t, dict):
            bi = _d(t['borne_inferieure'])
            bs = _d(t['borne_superieure']) if t.get('borne_superieure') is not None else None
            tx = _d(t['taux_irg'])
        else:
            bi = _d(t.borne_inferieure)
            bs = _d(t.borne_superieure) if t.borne_superieure is not None else None
            tx = _d(t.taux_irg)

        if i > 0 and seuils:
            prev_sup = seuils[-1][1]
            if prev_sup is not None and bi > prev_sup and bi <= prev_sup + 2:
                bi = prev_sup
        seuils.append((bi, bs, tx))

    detail = []
    for bi, bs, tx in seuils:
        if base_imposable <= bi:
            break
        montant = (min(base_imposable, bs) - bi) if bs is not None else (base_imposable - bi)
        if montant > 0:
            impot_tranche = _arrondir(montant * tx / Decimal('100'))
            detail.append({
                'borne_inf': int(bi),
                'borne_sup': int(bs) if bs is not None else None,
                'taux':      float(tx),
                'montant_tranche': int(montant),
                'impot_tranche':   int(impot_tranche),
            })

    return detail
