"""
Tests complets du moteur de simulation multi-barèmes – Guinée RTS/CNSS
=======================================================================
Barème officiel testé (CGI guinéen, 2019+) :
  Tranche 1 :        0 –  1 000 000 GNF →  0 %
  Tranche 2 :  1 000 000 –  5 000 000 GNF →  5 %
  Tranche 3 :  5 000 000 – 10 000 000 GNF → 10 %
  Tranche 4 : 10 000 000 – 20 000 000 GNF → 15 %
  Tranche 5 : > 20 000 000 GNF            → 20 %

Constantes utilisées :
  TAUX_CNSS_EMPLOYE = 5 %
  PLAFOND_CNSS      = 2 500 000 GNF
  Exonération       = 25 % du brut (plafond, arrondi floor)

Couverture :
  - Limites de chaque tranche RTS (0, 1M, 5M, 10M, 20M GNF)
  - Indemnités nulles, égales au plafond, largement supérieures (réintégration)
  - Plafond CNSS : brut < 2.5M, brut = 2.5M, brut > 2.5M
  - Brut très faible (sous SMIG) → RTS nulle
  - Zéro absolu (brut=0, indem=0) → pas de crash, tout = 0
  - Bruts au-delà de 20M (dernière tranche)
"""
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR


# ---------------------------------------------------------------------------
# Helpers (identiques au moteur de production)
# ---------------------------------------------------------------------------

def half_up(x) -> int:
    return int(Decimal(str(x)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def floor_gnf(x) -> int:
    return int(Decimal(str(x)).quantize(Decimal('1'), rounding=ROUND_FLOOR))


# ---------------------------------------------------------------------------
# Barème officiel 2019+
# ---------------------------------------------------------------------------

BAREME_5T = [
    {'borne_inf': 0,          'borne_sup': 1_000_000,  'taux': Decimal('0')},
    {'borne_inf': 1_000_000,  'borne_sup': 5_000_000,  'taux': Decimal('5')},
    {'borne_inf': 5_000_000,  'borne_sup': 10_000_000, 'taux': Decimal('10')},
    {'borne_inf': 10_000_000, 'borne_sup': 20_000_000, 'taux': Decimal('15')},
    {'borne_inf': 20_000_000, 'borne_sup': None,        'taux': Decimal('20')},
]

PLAFOND_CNSS = Decimal('2500000')
TAUX_CNSS    = Decimal('5')


def calcul_rts(base_rts_val, tranches=None):
    """Calcul progressif RTS par tranches. Retourne (rts_total, detail_list)."""
    if tranches is None:
        tranches = BAREME_5T
    base = Decimal(str(base_rts_val))
    if base <= 0:
        return 0, []
    total = Decimal('0')
    details = []
    for t in tranches:
        bi = Decimal(str(t['borne_inf']))
        bs = Decimal(str(t['borne_sup'])) if t['borne_sup'] is not None else None
        tx = Decimal(str(t['taux']))
        if base <= bi:
            break
        plafond = min(base, bs) if bs is not None else base
        bt = plafond - bi
        it = bt * tx / Decimal('100')
        total += it
        details.append({'tranche': f"[{int(bi):>12,} – {int(bs):>12,}]" if bs else f"[{int(bi):>12,} – ∞           ]",
                        'taux': float(tx), 'base_t': half_up(bt), 'impot_t': half_up(it)})
    return half_up(total), details


def bulletin(brut_val, indem_val, tranches=None):
    """Calcule le bulletin complet. Retourne un dict."""
    b = Decimal(str(brut_val))
    i = Decimal(str(max(0, indem_val)))

    cnss          = half_up(min(b, PLAFOND_CNSS) * TAUX_CNSS / Decimal('100'))
    plafond_exon  = floor_gnf(b * Decimal('25') / Decimal('100'))
    exon          = int(min(i, Decimal(str(plafond_exon))))
    depasse       = int(max(Decimal('0'), i - Decimal(str(plafond_exon))))
    base_rts      = max(0, int(b) - cnss - exon + depasse)
    rts, details  = calcul_rts(base_rts, tranches)
    net           = int(b) - cnss - rts
    taux_eff      = round(rts * 100 / base_rts, 2) if base_rts > 0 else 0.0

    return dict(brut=int(b), indem=int(i), cnss=cnss, plafond_exon=plafond_exon,
                exon=exon, depasse=depasse, base_rts=base_rts,
                rts=rts, net=net, taux_eff=taux_eff, details=details)


# ---------------------------------------------------------------------------
# Cas de tests
# Structure : (id, description, brut, indem, exp_cnss, exp_base_rts, exp_rts, exp_net)
# ---------------------------------------------------------------------------

TESTS = [
    # id    description                                brut        indem      cnss    base_rts      rts        net
    # NOTE: CNSS = min(brut, 2 500 000) × 5%  → plafonné à 125 000 GNF pour tout brut ≥ 2 500 000
    ("TC01", "Zéro absolu (brut=0, indem=0)",          0,          0,         0,       0,            0,         0),
    ("TC02", "Brut très faible 200 000 (< 1er seuil)", 200_000,    0,         10_000,  190_000,      0,         190_000),
    ("TC03", "Brut limite T1=1 000 000, indem=0",      1_000_000,  0,         50_000,  950_000,      0,         950_000),
    ("TC04", "Brut 2 000 000, indem=0 (dans T2 5%)",   2_000_000,  0,         100_000, 1_900_000,    45_000,    1_855_000),
    # brut ≥ 2.5M → CNSS plafonné à 125 000 GNF
    ("TC05", "Brut limite T2=5 000 000, indem=0",      5_000_000,  0,         125_000, 4_875_000,    193_750,   4_681_250),
    ("TC06", "Brut 7 000 000, indem=0 (dans T3 10%)",  7_000_000,  0,         125_000, 6_875_000,    387_500,   6_487_500),
    ("TC07", "Brut limite T3=10 000 000, indem=0",    10_000_000,  0,         125_000, 9_875_000,    687_500,   9_187_500),
    ("TC08", "Brut 15 000 000, indem=0 (dans T4 15%)",15_000_000,  0,         125_000, 14_875_000,   1_431_250, 13_443_750),
    ("TC09", "Brut limite T4=20 000 000, indem=0",    20_000_000,  0,         125_000, 19_875_000,   2_181_250, 17_693_750),
    ("TC10", "Brut 25 000 000, indem=0 (T5 20%)",     25_000_000,  0,         125_000, 24_875_000,   3_175_000, 21_700_000),
    # Plafond CNSS exact et dépassement
    ("TC11", "Brut=PLAFOND_CNSS 2 500 000, indem=0",   2_500_000,  0,         125_000, 2_375_000,    68_750,    2_306_250),
    ("TC12", "Brut au-dessus plafond CNSS 4 000 000",  4_000_000,  0,         125_000, 3_875_000,    143_750,   3_731_250),
    # Indemnités
    ("TC13", "Indem=0 (aucun avantage en nature)",     3_000_000,  0,         125_000, 2_875_000,    93_750,    2_781_250),
    ("TC14", "Indem < plafond 25% (pas de réintégr.)", 5_000_000,  1_000_000, 125_000, 3_875_000,    143_750,   4_731_250),
    ("TC15", "Indem = plafond 25% exactement",         5_000_000,  1_250_000, 125_000, 3_625_000,    131_250,   4_743_750),
    ("TC16", "Indem > plafond 25% (réintégration)",    3_000_000,  3_000_000, 125_000, 4_375_000,    168_750,   2_706_250),
    ("TC17", "Indem >> plafond, brut 5M indem 4M",     5_000_000,  4_000_000, 125_000, 6_375_000,    337_500,   4_537_500),
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def fmt(n):
    return f"{n:>15,}"


def run_tests():
    print("=" * 90)
    print("  TESTS MOTEUR SIMULATION MULTI-BARÈMES — BARÈME 5 TRANCHES OFFICIEL GUINÉE (2019+)")
    print("=" * 90)
    print(f"  {'ID':<6}  {'Description':<48}  {'Attendu':>10}  {'Obtenu':>10}  Statut")
    print("-" * 90)

    passed = 0
    failed = 0
    errors = []

    for row in TESTS:
        tid, desc, brut, indem, exp_cnss, exp_base_rts, exp_rts, exp_net = row
        try:
            r = bulletin(brut, indem)
        except Exception as exc:
            print(f"  {tid:<6}  {desc:<48}  EXCEPTION: {exc}")
            failed += 1
            errors.append(f"{tid}: exception — {exc}")
            continue

        checks = [
            ('cnss',     r['cnss'],     exp_cnss),
            ('base_rts', r['base_rts'], exp_base_rts),
            ('rts',      r['rts'],      exp_rts),
            ('net',      r['net'],      exp_net),
        ]
        ok = all(got == exp for _, got, exp in checks)
        status = "✅ OK" if ok else "❌ FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
            for field, got, exp in checks:
                if got != exp:
                    errors.append(f"{tid} [{field}]: attendu={exp:,}  obtenu={got:,}")

        # Print summary line (rts vs expected rts)
        print(f"  {tid:<6}  {desc:<48}  {exp_rts:>10,}  {r['rts']:>10,}  {status}")

    print("-" * 90)
    print(f"  {passed} réussis, {failed} échoués sur {len(TESTS)} tests")
    if errors:
        print()
        print("  DÉTAIL DES ERREURS :")
        for e in errors:
            print(f"    • {e}")
    print("=" * 90)

    # Détail des tranches pour un cas représentatif
    print()
    print("  DÉTAIL TRANCHES — TC17 (brut=5M, indem=4M, réintégration maximale)")
    print("-" * 90)
    r = bulletin(5_000_000, 4_000_000)
    print(f"    Brut            : {r['brut']:>15,} GNF")
    print(f"    Indemnités      : {r['indem']:>15,} GNF")
    print(f"    CNSS            : {r['cnss']:>15,} GNF")
    print(f"    Plafond exon.   : {r['plafond_exon']:>15,} GNF  (25% brut, arrondi floor)")
    print(f"    Exonéré         : {r['exon']:>15,} GNF")
    print(f"    Dépassement     : {r['depasse']:>15,} GNF  (réintégré dans base RTS)")
    print(f"    Base RTS        : {r['base_rts']:>15,} GNF")
    for d in r['details']:
        print(f"      {d['tranche']}  {d['taux']:>5.1f}%  base={d['base_t']:>12,}  impôt={d['impot_t']:>12,}")
    print(f"    RTS total       : {r['rts']:>15,} GNF")
    print(f"    Taux effectif   : {r['taux_eff']:>15.2f} %")
    print(f"    Net             : {r['net']:>15,} GNF")
    print("=" * 90)
    return failed == 0


if __name__ == '__main__':
    import sys
    ok = run_tests()
    sys.exit(0 if ok else 1)
