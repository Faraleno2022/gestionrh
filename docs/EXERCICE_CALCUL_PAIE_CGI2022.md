# EXERCICE PRATIQUE - CALCUL DE PAIE
## Conforme CGI 2022 + Code du Travail guinéen

---

# DONNÉES DE L'EXERCICE

## Employé : Mamadou DIALLO

| Information | Valeur |
|-------------|--------|
| Matricule | EMP-2025-001 |
| Poste | Ingénieur Informatique |
| Date embauche | 15/03/2020 |
| Ancienneté | 4 ans et 9 mois |
| Situation familiale | Marié, 3 enfants |

## Éléments de rémunération (Janvier 2026)

| Rubrique | Montant |
|----------|---------|
| Salaire de base | 5 000 000 GNF |
| Prime de responsabilité | 500 000 GNF |
| Indemnité de transport | 300 000 GNF |
| Indemnité de logement | 400 000 GNF |
| Heures supplémentaires (4 prem.) | 8 heures |
| Heures supplémentaires (au-delà) | 6 heures |

---

# MÉTHODE DE CALCUL DÉTAILLÉE

## ÉTAPE 1 : Calcul du Salaire Brut

### 1.1 Taux horaire

```
Taux horaire = Salaire de base / 173,33
Taux horaire = 5 000 000 / 173,33 = 28 847 GNF
```

### 1.2 Heures supplémentaires (Art. 221)

| Type HS | Heures | Taux | Montant |
|---------|--------|------|---------|
| 4 premières HS (+30%) | 8h | 130% | 300 008 GNF |
| Au-delà (+60%) | 6h | 160% | 276 931 GNF |
| **Total HS** | | | **576 939 GNF** |

### 1.3 Salaire Brut Total

| Élément | Montant |
|---------|---------|
| Salaire de base | 5 000 000 GNF |
| Prime de responsabilité | 500 000 GNF |
| Indemnité de transport | 300 000 GNF |
| Indemnité de logement | 400 000 GNF |
| Heures supplémentaires | 576 939 GNF |
| **SALAIRE BRUT** | **6 776 939 GNF** |

---

## ÉTAPE 2 : Plafond 25% Indemnités

```
Indemnités = 300 000 + 400 000 = 700 000 GNF
Plafond = 6 776 939 × 25% = 1 694 235 GNF
700 000 < 1 694 235 → CONFORME ✅
```

---

## ÉTAPE 3 : Calcul CNSS

### Règles
- Plancher : 550 000 GNF
- Plafond : 2 500 000 GNF
- Taux salarié : 5%
- Taux employeur : 18%

### Calcul

```
Brut = 6 776 939 GNF > Plafond 2 500 000 GNF
→ Assiette CNSS = 2 500 000 GNF (plafond)

CNSS Employé = 2 500 000 × 5% = 125 000 GNF
CNSS Employeur = 2 500 000 × 18% = 450 000 GNF
```

---

## ÉTAPE 4 : Calcul RTS (CGI 2022 - 6 tranches)

### Base imposable

```
Base imposable = Brut - CNSS Employé
Base imposable = 6 776 939 - 125 000 = 6 651 939 GNF
```

### Barème RTS CGI 2022 (6 tranches)

| Tranche | Bornes | Taux |
|---------|--------|------|
| 1 | 0 - 1 000 000 | 0% |
| 2 | 1 000 001 - 3 000 000 | 5% |
| 3 | 3 000 001 - 5 000 000 | 8% |
| 4 | 5 000 001 - 10 000 000 | 10% |
| 5 | 10 000 001 - 20 000 000 | 15% |
| 6 | > 20 000 000 | 20% |

### Calcul détaillé RTS

| Tranche | Montant imposé | Taux | RTS |
|---------|----------------|------|-----|
| 1 | 1 000 000 | 0% | 0 GNF |
| 2 | 2 000 000 | 5% | 100 000 GNF |
| 3 | 2 000 000 | 8% | 160 000 GNF |
| 4 | 1 651 939 | 10% | 165 194 GNF |
| **TOTAL RTS** | | | **425 194 GNF** |

---

## ÉTAPE 5 : Charges Patronales

| Charge | Taux | Base | Montant |
|--------|------|------|---------|
| CNSS Employeur | 18% | 2 500 000 | 450 000 GNF |
| VF | 6% | 6 776 939 | 406 616 GNF |
| TA | 1,5% | 6 776 939 | 101 654 GNF |
| **TOTAL** | | | **958 270 GNF** |

---

## ÉTAPE 6 : Net à Payer

```
Net = Brut - CNSS Employé - RTS
Net = 6 776 939 - 125 000 - 425 194
Net = 6 226 745 GNF
```

---

# RÉCAPITULATIF BULLETIN

| Élément | Montant |
|---------|---------|
| **SALAIRE BRUT** | **6 776 939 GNF** |
| CNSS Employé (5%) | - 125 000 GNF |
| RTS (IRG) | - 425 194 GNF |
| **NET À PAYER** | **6 226 745 GNF** |

## Charges patronales

| Charge | Montant |
|--------|---------|
| CNSS Employeur (18%) | 450 000 GNF |
| Versement Forfaitaire (6%) | 406 616 GNF |
| Taxe Apprentissage (1,5%) | 101 654 GNF |
| **TOTAL CHARGES** | **958 270 GNF** |

## Coût total employeur

```
Coût = Brut + Charges patronales
Coût = 6 776 939 + 958 270 = 7 735 209 GNF
```

---

# CONFORMITÉ CGI 2022

| Règle | Statut |
|-------|--------|
| RTS 6 tranches (avec 8%) | ✅ |
| CNSS plafond 2 500 000 | ✅ |
| CNSS plancher 550 000 | ✅ |
| CNSS salarié 5% | ✅ |
| CNSS employeur 18% | ✅ |
| VF 6% | ✅ |
| TA 1,5% | ✅ |
| HS Art. 221 (130%/160%) | ✅ |
| Plafond indemnités 25% | ✅ |

---

*Document généré le 02/01/2026 - GuineeRH.space*
