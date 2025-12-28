# MANUEL D'UTILISATION - GESTIONNAIRE RH GUINÉE
## Module Paie - Version 2.0
### Conforme à la législation guinéenne 2025

---

# TABLE DES MATIÈRES

1. [Introduction](#1-introduction)
2. [Cadre Légal](#2-cadre-légal)
3. [Cotisations CNSS](#3-cotisations-cnss)
4. [Retenue sur Traitements et Salaires (RTS)](#4-retenue-sur-traitements-et-salaires-rts)
5. [Charges Patronales](#5-charges-patronales)
6. [Exonérations et Cas Particuliers](#6-exonérations-et-cas-particuliers)
7. [Exemples de Calcul Complets](#7-exemples-de-calcul-complets)
8. [Déclarations Sociales](#8-déclarations-sociales)
9. [Alertes et Échéances](#9-alertes-et-échéances)
10. [Commandes de Gestion](#10-commandes-de-gestion)

---

# 1. INTRODUCTION

## 1.1 Présentation

Le Gestionnaire RH Guinée est une application complète de gestion des ressources humaines conforme à la législation guinéenne. Ce manuel détaille les méthodes de calcul de la paie selon :

- Le **Code du Travail guinéen**
- Les règlements de la **Caisse Nationale de Sécurité Sociale (CNSS)**
- Le **Code Général des Impôts (CGI)** - Version 2022+
- Les directives de la **Direction Nationale des Impôts (DNI)**

## 1.2 Principes Fondamentaux

### Obligation de Déclaration Universelle

> **IMPORTANT** : En Guinée, **TOUS les salariés doivent être déclarés**, quel que soit leur niveau de salaire.
> Les exonérations concernent uniquement le **calcul des impôts et cotisations**, PAS l'obligation de déclaration.

### Échéances

| Déclaration | Échéance | Pénalité de retard |
|-------------|----------|-------------------|
| CNSS | 15 du mois suivant | 5% par mois |
| RTS | 15 du mois suivant | 100% du montant dû |
| VF | 15 du mois suivant | 100% du montant dû |

---

# 2. CADRE LÉGAL

## 2.1 Références Légales

| Texte | Application |
|-------|-------------|
| Code du Travail | Contrats, salaires, heures supplémentaires |
| Code Général des Impôts 2022 | Barème RTS, VF, Taxe d'Apprentissage |
| Décrets CNSS | Taux, plancher, plafond |
| Arrêtés ministériels | SMIG, indemnités |

## 2.2 Constantes Légales 2025

| Constante | Valeur | Description |
|-----------|--------|-------------|
| SMIG | 550 000 GNF | Salaire Minimum Interprofessionnel Garanti |
| Plancher CNSS | 550 000 GNF | Assiette minimale de cotisation |
| Plafond CNSS | 2 500 000 GNF | Assiette maximale de cotisation |
| Heures légales/semaine | 40 heures | Durée légale du travail |
| Heures légales/mois | 173,33 heures | 40h × 52 semaines / 12 mois |
| Jours ouvrables/mois | 22 jours | Moyenne mensuelle |

---

# 3. COTISATIONS CNSS

## 3.1 Taux de Cotisation

| Part | Taux | Répartition |
|------|------|-------------|
| **Employé** | **5%** | Retraite 2,5% + Maladie 2,5% |
| **Employeur** | **18%** | Prestations familiales 6% + AT/MP 4% + Retraite 4% + Maladie 4% |
| **Total** | **23%** | - |

## 3.2 Règle du Plancher et Plafond

### Principe

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ASSIETTE CNSS                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Si Salaire < 550 000 GNF    →  Assiette = 550 000 GNF (plancher)  │
│                                                                      │
│   Si 550 000 ≤ Salaire ≤ 2 500 000 GNF  →  Assiette = Salaire réel  │
│                                                                      │
│   Si Salaire > 2 500 000 GNF  →  Assiette = 2 500 000 GNF (plafond) │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Formule de Calcul

```
Assiette CNSS = MIN( MAX(Salaire_Brut, PLANCHER), PLAFOND )

CNSS Employé = Assiette CNSS × 5%
CNSS Employeur = Assiette CNSS × 18%
```

### Cas Particulier : Salaire Très Faible

Si le salaire brut est inférieur à **10% du plancher** (55 000 GNF), aucune cotisation CNSS n'est prélevée. Cela concerne les cas de congé sans solde ou d'absence prolongée.

## 3.3 Exemples de Calcul CNSS

### Exemple 1 : Salaire sous le plancher (400 000 GNF)

```
Salaire brut         : 400 000 GNF
Plancher CNSS        : 550 000 GNF
Assiette CNSS        : 550 000 GNF (on applique le plancher)

CNSS Employé (5%)    : 550 000 × 5% = 27 500 GNF
CNSS Employeur (18%) : 550 000 × 18% = 99 000 GNF
```

### Exemple 2 : Salaire entre plancher et plafond (1 500 000 GNF)

```
Salaire brut         : 1 500 000 GNF
Assiette CNSS        : 1 500 000 GNF (salaire réel)

CNSS Employé (5%)    : 1 500 000 × 5% = 75 000 GNF
CNSS Employeur (18%) : 1 500 000 × 18% = 270 000 GNF
```

### Exemple 3 : Salaire au-dessus du plafond (8 000 000 GNF)

```
Salaire brut         : 8 000 000 GNF
Plafond CNSS         : 2 500 000 GNF
Assiette CNSS        : 2 500 000 GNF (on applique le plafond)

CNSS Employé (5%)    : 2 500 000 × 5% = 125 000 GNF
CNSS Employeur (18%) : 2 500 000 × 18% = 450 000 GNF
```

---

# 4. RETENUE SUR TRAITEMENTS ET SALAIRES (RTS)

## 4.1 Principe de l'Impôt Progressif

La RTS est un **impôt progressif par tranches**. Chaque tranche de revenu est imposée à son propre taux. Ce n'est pas le revenu total qui est imposé au taux de la tranche la plus élevée.

## 4.2 Barème RTS 2022+ (Code Général des Impôts)

| Tranche | Revenus mensuels | Taux | Impôt max de la tranche |
|---------|------------------|------|------------------------|
| 1 | 0 - 1 000 000 GNF | **0%** | 0 GNF |
| 2 | 1 000 001 - 3 000 000 GNF | **5%** | 100 000 GNF |
| 3 | 3 000 001 - 5 000 000 GNF | **8%** | 160 000 GNF |
| 4 | 5 000 001 - 10 000 000 GNF | **10%** | 500 000 GNF |
| 5 | 10 000 001 - 20 000 000 GNF | **15%** | 1 500 000 GNF |
| 6 | Au-delà de 20 000 000 GNF | **20%** | Variable |

> **Note** : La tranche 3 (8%) a été ajoutée par le CGI 2022. Les anciens barèmes n'avaient que 5 tranches.

## 4.3 Base Imposable RTS

```
Base Imposable RTS = Salaire Brut - CNSS Employé - Déductions
```

### Déductions Possibles

| Déduction | Montant | Condition |
|-----------|---------|-----------|
| Conjoint | 100 000 GNF | Marié(e) |
| Enfant à charge | 50 000 GNF/enfant | Max 4 enfants |
| Abattement professionnel | 5% de la base | Plafonné à 1 000 000 GNF |

## 4.4 Méthode de Calcul RTS

### Algorithme

```
Pour chaque tranche (de la plus basse à la plus haute) :
    Si Base_Imposable >= Borne_Inférieure :
        Montant_dans_tranche = MIN(Base_Imposable, Borne_Supérieure) - Borne_Inférieure + 1
        Impôt_tranche = Montant_dans_tranche × Taux
        RTS_Total += Impôt_tranche
```

### Exemple Détaillé : Base imposable de 7 875 000 GNF

```
┌────────────────────────────────────────────────────────────────────────┐
│ CALCUL RTS DÉTAILLÉ - Base imposable : 7 875 000 GNF                   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│ Tranche 1 (0% sur 0 - 1 000 000 GNF)                                  │
│   Montant : 1 000 000 GNF × 0% = 0 GNF                                │
│                                                                        │
│ Tranche 2 (5% sur 1 000 001 - 3 000 000 GNF)                          │
│   Montant : 2 000 000 GNF × 5% = 100 000 GNF                          │
│                                                                        │
│ Tranche 3 (8% sur 3 000 001 - 5 000 000 GNF)                          │
│   Montant : 2 000 000 GNF × 8% = 160 000 GNF                          │
│                                                                        │
│ Tranche 4 (10% sur 5 000 001 - 7 875 000 GNF)                         │
│   Montant : 2 875 000 GNF × 10% = 287 500 GNF                         │
│                                                                        │
├────────────────────────────────────────────────────────────────────────┤
│ TOTAL RTS = 0 + 100 000 + 160 000 + 287 500 = 547 500 GNF             │
└────────────────────────────────────────────────────────────────────────┘
```

---

# 5. CHARGES PATRONALES

## 5.1 Récapitulatif des Charges Patronales

| Charge | Taux | Assiette | Description |
|--------|------|----------|-------------|
| **CNSS Employeur** | **18%** | Assiette CNSS (550K - 2,5M) | Cotisation sociale |
| **Versement Forfaitaire (VF)** | **6%** | Salaire brut total | Impôt sur la masse salariale |
| **Taxe d'Apprentissage (TA)** | **1,5%** | Salaire brut total | Formation professionnelle |
| **TOTAL** | **25,5%** | Variable | - |

## 5.2 Différence entre Assiettes

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ASSIETTES DE CALCUL                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  CNSS Employeur (18%)                                               │
│  └── Assiette = MIN(MAX(Brut, 550K), 2,5M)  ← Plafonnée             │
│                                                                      │
│  Versement Forfaitaire (6%)                                         │
│  └── Assiette = Salaire Brut Total  ← Non plafonnée                 │
│                                                                      │
│  Taxe d'Apprentissage (1,5%)                                        │
│  └── Assiette = Salaire Brut Total  ← Non plafonnée                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 5.3 Exemple de Calcul des Charges Patronales

### Salaire brut : 8 000 000 GNF

```
┌─────────────────────────────────────────────────────────────────────┐
│ CHARGES PATRONALES - Salaire brut : 8 000 000 GNF                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ 1. CNSS Employeur (18%)                                             │
│    Assiette CNSS = 2 500 000 GNF (plafond)                          │
│    CNSS Employeur = 2 500 000 × 18% = 450 000 GNF                   │
│                                                                      │
│ 2. Versement Forfaitaire (6%)                                       │
│    Assiette VF = 8 000 000 GNF (brut total)                         │
│    VF = 8 000 000 × 6% = 480 000 GNF                                │
│                                                                      │
│ 3. Taxe d'Apprentissage (1,5%)                                      │
│    Assiette TA = 8 000 000 GNF (brut total)                         │
│    TA = 8 000 000 × 1,5% = 120 000 GNF                              │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│ TOTAL CHARGES PATRONALES = 450 000 + 480 000 + 120 000              │
│                          = 1 050 000 GNF                            │
│                                                                      │
│ COÛT TOTAL EMPLOYEUR = 8 000 000 + 1 050 000 = 9 050 000 GNF        │
└─────────────────────────────────────────────────────────────────────┘
```

---

# 6. EXONÉRATIONS ET CAS PARTICULIERS

## 6.1 Exonération RTS pour Stagiaires et Apprentis

### Conditions d'Éligibilité

| Critère | Condition |
|---------|-----------|
| Type de contrat | Stage ou Apprentissage |
| Durée maximale | 12 mois depuis le début du contrat |
| Indemnité maximale | ≤ 1 200 000 GNF/mois |

### Règle de Calcul

```
SI (type_contrat IN ['stage', 'apprentissage'])
   ET (durée_contrat ≤ 12 mois)
   ET (indemnité ≤ 1 200 000 GNF)
ALORS
   RTS = 0 GNF (exonéré)
SINON
   RTS = calcul normal selon barème
```

### Exemple : Stagiaire avec indemnité de 900 000 GNF

```
Type de contrat     : Stage
Durée               : 6 mois (≤ 12 mois ✓)
Indemnité           : 900 000 GNF (≤ 1 200 000 GNF ✓)

→ EXONÉRÉ de RTS

Calcul :
  Salaire brut      : 900 000 GNF
  CNSS Employé      : 550 000 × 5% = 27 500 GNF (plancher appliqué)
  RTS               : 0 GNF (exonéré)
  Net à payer       : 900 000 - 27 500 = 872 500 GNF
```

## 6.2 Plafond 25% des Indemnités Forfaitaires

### Principe

Les indemnités forfaitaires (logement, transport, panier) sont exonérées de RTS dans la limite de **25% du salaire brut**. L'excédent est réintégré dans la base imposable.

### Indemnités Concernées

- Prime de transport / Allocation transport
- Allocation logement / Indemnité de logement
- Indemnité de repas / Prime de panier

### Formule

```
Plafond_Indemnités = Salaire_Brut × 25%

SI Total_Indemnités > Plafond_Indemnités ALORS
   Excédent = Total_Indemnités - Plafond_Indemnités
   Base_Imposable += Excédent  (réintégration)
```

### Exemple : Dépassement du plafond 25%

```
┌─────────────────────────────────────────────────────────────────────┐
│ VÉRIFICATION PLAFOND 25% INDEMNITÉS                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ Salaire de base        : 2 000 000 GNF                              │
│ Prime de transport     : 400 000 GNF                                │
│ Allocation logement    : 300 000 GNF                                │
│ ─────────────────────────────────                                   │
│ Salaire brut           : 2 700 000 GNF                              │
│ Total indemnités       : 700 000 GNF                                │
│                                                                      │
│ Plafond 25%            : 2 700 000 × 25% = 675 000 GNF              │
│                                                                      │
│ Dépassement            : 700 000 - 675 000 = 25 000 GNF             │
│                                                                      │
│ → 25 000 GNF réintégrés dans la base imposable RTS                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

# 7. EXEMPLES DE CALCUL COMPLETS

## 7.1 Exemple 1 : Cadre Supérieur (8 000 000 GNF)

```
╔═══════════════════════════════════════════════════════════════════════╗
║                    BULLETIN DE PAIE - EXEMPLE 1                        ║
║                    Cadre Supérieur                                     ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║ DONNÉES D'ENTRÉE                                                       ║
║ ────────────────                                                       ║
║ Salaire de base           : 7 500 000 GNF                             ║
║ Prime de responsabilité   : 500 000 GNF                               ║
║ ─────────────────────────────────────────                             ║
║ SALAIRE BRUT              : 8 000 000 GNF                             ║
║                                                                        ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║ ÉTAPE 1 : CALCUL CNSS                                                 ║
║ ─────────────────────                                                 ║
║ Assiette CNSS = MIN(8 000 000, 2 500 000) = 2 500 000 GNF (plafond)   ║
║ CNSS Employé = 2 500 000 × 5% = 125 000 GNF                           ║
║                                                                        ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║ ÉTAPE 2 : CALCUL BASE IMPOSABLE RTS                                   ║
║ ───────────────────────────────────                                   ║
║ Base imposable = Brut - CNSS Employé                                  ║
║                = 8 000 000 - 125 000 = 7 875 000 GNF                  ║
║                                                                        ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║ ÉTAPE 3 : CALCUL RTS (BARÈME PROGRESSIF)                              ║
║ ────────────────────────────────────────                              ║
║                                                                        ║
║ Tranche 1 : 0 - 1 000 000 GNF × 0%                                    ║
║           = 1 000 000 × 0% = 0 GNF                                    ║
║                                                                        ║
║ Tranche 2 : 1 000 001 - 3 000 000 GNF × 5%                            ║
║           = 2 000 000 × 5% = 100 000 GNF                              ║
║                                                                        ║
║ Tranche 3 : 3 000 001 - 5 000 000 GNF × 8%                            ║
║           = 2 000 000 × 8% = 160 000 GNF                              ║
║                                                                        ║
║ Tranche 4 : 5 000 001 - 7 875 000 GNF × 10%                           ║
║           = 2 875 000 × 10% = 287 500 GNF                             ║
║                                                                        ║
║ TOTAL RTS = 0 + 100 000 + 160 000 + 287 500 = 547 500 GNF             ║
║                                                                        ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║ ÉTAPE 4 : CALCUL NET À PAYER                                          ║
║ ────────────────────────────                                          ║
║ Total retenues = CNSS + RTS = 125 000 + 547 500 = 672 500 GNF         ║
║ NET À PAYER = 8 000 000 - 672 500 = 7 327 500 GNF                     ║
║                                                                        ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║ CHARGES PATRONALES (non visibles sur le bulletin)                     ║
║ ─────────────────────────────────────────────────                     ║
║ CNSS Employeur    : 2 500 000 × 18% = 450 000 GNF                     ║
║ Versement Forfait.: 8 000 000 × 6%  = 480 000 GNF                     ║
║ Taxe Apprentissage: 8 000 000 × 1,5%= 120 000 GNF                     ║
║ ─────────────────────────────────────────────────                     ║
║ TOTAL CHARGES     : 1 050 000 GNF                                     ║
║                                                                        ║
║ COÛT TOTAL EMPLOYEUR : 8 000 000 + 1 050 000 = 9 050 000 GNF          ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

## 7.2 Exemple 2 : Employé Standard (1 500 000 GNF)

```
╔═══════════════════════════════════════════════════════════════════════╗
║                    BULLETIN DE PAIE - EXEMPLE 2                        ║
║                    Employé Standard                                    ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║ DONNÉES D'ENTRÉE                                                       ║
║ Salaire de base           : 1 200 000 GNF                             ║
║ Prime de transport        : 200 000 GNF                               ║
║ Prime d'ancienneté        : 100 000 GNF                               ║
║ ─────────────────────────────────────────                             ║
║ SALAIRE BRUT              : 1 500 000 GNF                             ║
║                                                                        ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║ CALCUL CNSS                                                           ║
║ Assiette CNSS = 1 500 000 GNF (entre plancher et plafond)             ║
║ CNSS Employé = 1 500 000 × 5% = 75 000 GNF                            ║
║                                                                        ║
║ CALCUL RTS                                                            ║
║ Base imposable = 1 500 000 - 75 000 = 1 425 000 GNF                   ║
║                                                                        ║
║ Tranche 1 : 1 000 000 × 0% = 0 GNF                                    ║
║ Tranche 2 : 425 000 × 5% = 21 250 GNF                                 ║
║ TOTAL RTS = 21 250 GNF                                                ║
║                                                                        ║
║ NET À PAYER = 1 500 000 - 75 000 - 21 250 = 1 403 750 GNF             ║
║                                                                        ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║ CHARGES PATRONALES                                                    ║
║ CNSS Employeur    : 1 500 000 × 18% = 270 000 GNF                     ║
║ Versement Forfait.: 1 500 000 × 6%  = 90 000 GNF                      ║
║ Taxe Apprentissage: 1 500 000 × 1,5%= 22 500 GNF                      ║
║ TOTAL CHARGES     : 382 500 GNF                                       ║
║                                                                        ║
║ COÛT TOTAL EMPLOYEUR : 1 882 500 GNF                                  ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

## 7.3 Exemple 3 : Stagiaire Exonéré (800 000 GNF)

```
╔═══════════════════════════════════════════════════════════════════════╗
║                    BULLETIN DE PAIE - EXEMPLE 3                        ║
║                    Stagiaire (Exonéré RTS)                            ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║ DONNÉES D'ENTRÉE                                                       ║
║ Type de contrat           : Stage                                     ║
║ Durée du stage            : 6 mois (≤ 12 mois ✓)                      ║
║ Indemnité de stage        : 800 000 GNF (≤ 1 200 000 GNF ✓)           ║
║                                                                        ║
║ → ÉLIGIBLE À L'EXONÉRATION RTS                                        ║
║                                                                        ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║ CALCUL CNSS                                                           ║
║ Assiette CNSS = 550 000 GNF (plancher appliqué car 800K < 550K ✗)     ║
║ Correction : 800 000 > 550 000, donc Assiette = 800 000 GNF           ║
║ CNSS Employé = 800 000 × 5% = 40 000 GNF                              ║
║                                                                        ║
║ CALCUL RTS                                                            ║
║ RTS = 0 GNF (EXONÉRÉ - Stagiaire éligible)                            ║
║                                                                        ║
║ NET À PAYER = 800 000 - 40 000 = 760 000 GNF                          ║
║                                                                        ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║ CHARGES PATRONALES                                                    ║
║ CNSS Employeur    : 800 000 × 18% = 144 000 GNF                       ║
║ Versement Forfait.: 800 000 × 6%  = 48 000 GNF                        ║
║ Taxe Apprentissage: 800 000 × 1,5%= 12 000 GNF                        ║
║ TOTAL CHARGES     : 204 000 GNF                                       ║
║                                                                        ║
║ COÛT TOTAL EMPLOYEUR : 1 004 000 GNF                                  ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

## 7.4 Exemple 4 : Employé au SMIG (550 000 GNF)

```
╔═══════════════════════════════════════════════════════════════════════╗
║                    BULLETIN DE PAIE - EXEMPLE 4                        ║
║                    Employé au SMIG                                     ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║ DONNÉES D'ENTRÉE                                                       ║
║ Salaire de base (SMIG)    : 550 000 GNF                               ║
║                                                                        ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║ CALCUL CNSS                                                           ║
║ Assiette CNSS = 550 000 GNF (= plancher)                              ║
║ CNSS Employé = 550 000 × 5% = 27 500 GNF                              ║
║                                                                        ║
║ CALCUL RTS                                                            ║
║ Base imposable = 550 000 - 27 500 = 522 500 GNF                       ║
║ Tranche 1 : 522 500 × 0% = 0 GNF (< 1 000 000 GNF)                    ║
║ TOTAL RTS = 0 GNF                                                     ║
║                                                                        ║
║ NET À PAYER = 550 000 - 27 500 - 0 = 522 500 GNF                      ║
║                                                                        ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║ CHARGES PATRONALES                                                    ║
║ CNSS Employeur    : 550 000 × 18% = 99 000 GNF                        ║
║ Versement Forfait.: 550 000 × 6%  = 33 000 GNF                        ║
║ Taxe Apprentissage: 550 000 × 1,5%= 8 250 GNF                         ║
║ TOTAL CHARGES     : 140 250 GNF                                       ║
║                                                                        ║
║ COÛT TOTAL EMPLOYEUR : 690 250 GNF                                    ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

# 8. DÉCLARATIONS SOCIALES

## 8.1 Types de Déclarations

| Déclaration | Organisme | Contenu | Échéance |
|-------------|-----------|---------|----------|
| CNSS | Caisse Nationale de Sécurité Sociale | Cotisations employé + employeur | 15 du mois suivant |
| RTS | Direction Nationale des Impôts | Retenue sur salaires | 15 du mois suivant |
| VF | Direction Nationale des Impôts | Versement Forfaitaire 6% | 15 du mois suivant |
| DMU | Direction Nationale des Impôts | Déclaration Mensuelle Unique | 15 du mois suivant |

## 8.2 Calcul des Montants à Déclarer

### Déclaration CNSS

```
Total CNSS à verser = Σ (CNSS Employé + CNSS Employeur) pour tous les employés

Exemple pour 10 employés avec masse salariale de 20 000 000 GNF :
- Si tous les salaires sont entre plancher et plafond :
  CNSS Employé total  = 20 000 000 × 5%  = 1 000 000 GNF
  CNSS Employeur total = 20 000 000 × 18% = 3 600 000 GNF
  TOTAL À VERSER = 4 600 000 GNF
```

### Déclaration RTS

```
Total RTS à verser = Σ RTS de tous les employés
```

### Déclaration VF

```
Total VF à verser = Masse salariale brute × 6%
```

---

# 9. ALERTES ET ÉCHÉANCES

## 9.1 Système d'Alertes

L'application génère automatiquement des alertes pour les échéances de déclarations :

| Jours avant échéance | Niveau | Statut |
|---------------------|--------|--------|
| > 5 jours | ℹ️ Information | À venir |
| 3-5 jours | ⚠️ Avertissement | À venir |
| 1-3 jours | ⚠️ Avertissement | Urgent |
| ≤ 1 jour | 🚨 Danger | Urgent |
| Dépassé | 🚨 Danger | En retard |

## 9.2 Pénalités de Retard

| Déclaration | Pénalité |
|-------------|----------|
| CNSS | 5% par mois de retard |
| RTS/VF | 100% du montant dû |

## 9.3 Commande de Génération des Alertes

```bash
# Générer les alertes pour le mois en cours
python manage.py generer_alertes_echeances

# Générer pour un mois spécifique
python manage.py generer_alertes_echeances --mois 12 --annee 2025

# Actualiser toutes les alertes existantes
python manage.py generer_alertes_echeances --actualiser
```

---

# 10. COMMANDES DE GESTION

## 10.1 Commandes Disponibles

| Commande | Description |
|----------|-------------|
| `python manage.py init_paie_guinee` | Initialise les constantes et barèmes |
| `python manage.py update_bareme_rts` | Met à jour le barème RTS |
| `python manage.py update_cnss_constants` | Met à jour les constantes CNSS |
| `python manage.py recalculer_bulletins` | Recalcule les bulletins de paie |
| `python manage.py test_calculs_paie` | Teste l'exactitude des calculs |
| `python manage.py generer_alertes_echeances` | Génère les alertes d'échéances |

## 10.2 Exemples d'Utilisation

### Recalculer les bulletins d'une période

```bash
# Simulation (dry-run)
python manage.py recalculer_bulletins --periode 12 --annee 2025 --dry-run

# Application réelle
python manage.py recalculer_bulletins --periode 12 --annee 2025
```

### Tester les calculs

```bash
python manage.py test_calculs_paie
```

Résultat attendu :
```
======================================================================
TESTS DE VÉRIFICATION DES CALCULS DE PAIE - GUINÉE
======================================================================
📊 TEST 1: CALCUL CNSS (Plancher/Plafond) - 6/6 ✓
📊 TEST 2: BARÈME RTS 2022+ (avec tranche 8%) - 10/10 ✓
📊 TEST 3: CHARGES PATRONALES (CNSS 18% + VF 6% + TA 1.5%) - 3/3 ✓
📊 TEST 4: EXEMPLE COMPLET DU MANUEL (8 000 000 GNF) - 8/8 ✓
📊 TEST 5: EXONÉRATION RTS STAGIAIRES/APPRENTIS - 9/9 ✓
📊 TEST 6: PLAFOND 25% INDEMNITÉS FORFAITAIRES - 6/6 ✓
======================================================================
✅ TOUS LES TESTS RÉUSSIS: 42/42
======================================================================
```

---

# ANNEXES

## A. Tableau Récapitulatif des Taux

| Élément | Taux | Assiette |
|---------|------|----------|
| CNSS Employé | 5% | Plafonnée (550K - 2,5M) |
| CNSS Employeur | 18% | Plafonnée (550K - 2,5M) |
| Versement Forfaitaire | 6% | Brut total |
| Taxe d'Apprentissage | 1,5% | Brut total |
| RTS Tranche 1 | 0% | 0 - 1M |
| RTS Tranche 2 | 5% | 1M - 3M |
| RTS Tranche 3 | 8% | 3M - 5M |
| RTS Tranche 4 | 10% | 5M - 10M |
| RTS Tranche 5 | 15% | 10M - 20M |
| RTS Tranche 6 | 20% | > 20M |

## B. Contacts Utiles

| Organisme | Contact |
|-----------|---------|
| CNSS | www.cnss.gov.gn |
| DNI | www.dni.gov.gn |
| Ministère du Travail | www.travail.gov.gn |

## C. Historique des Versions

| Version | Date | Modifications |
|---------|------|---------------|
| 1.0 | Nov 2025 | Version initiale |
| 1.1 | Déc 2025 | Correction barème RTS, ajout VF/TA |
| 2.0 | Déc 2025 | Exonérations stagiaires, plafond 25%, alertes |

---

**Document généré par Gestionnaire RH Guinée**
**Version 2.0 - Décembre 2025**
**www.guineerh.space**
