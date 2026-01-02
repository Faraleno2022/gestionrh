# DOSSIER DE SOUMISSION OFFICIELLE
## Système de Paie GuineeRH.space
### Demande d'agrément / Certification de conformité

---

**Soumis à** : Direction Générale des Impôts (DGI) / CNSS / Ministère du Travail  
**Date** : 02 Janvier 2026  
**Référence** : GUINEEHR-2026-001  

---

# I. IDENTIFICATION DU DEMANDEUR

## 1.1 Éditeur du logiciel

| Information | Valeur |
|-------------|--------|
| Nom commercial | GuineeRH.space |
| Forme juridique | [À compléter] |
| NIF | [À compléter] |
| RCCM | [À compléter] |
| Adresse | [À compléter] |
| Téléphone | [À compléter] |
| Email | contact@guineehr.space |
| Site web | https://guineehr.space |

## 1.2 Responsable technique

| Information | Valeur |
|-------------|--------|
| Nom | [À compléter] |
| Fonction | Directeur Technique |
| Téléphone | [À compléter] |
| Email | [À compléter] |

---

# II. PRÉSENTATION DU LOGICIEL

## 2.1 Description générale

GuineeRH.space est un système intégré de gestion des ressources humaines et de la paie, spécialement conçu pour le contexte guinéen et conforme à la législation en vigueur.

## 2.2 Fonctionnalités principales

| Module | Description |
|--------|-------------|
| Gestion employés | Dossiers, contrats, carrières |
| Calcul paie | Salaires, cotisations, impôts |
| Déclarations | CNSS, DGI, exports |
| Bulletins | Génération PDF, envoi email |
| Reporting | Tableaux de bord, statistiques |

## 2.3 Technologies utilisées

| Composant | Technologie |
|-----------|-------------|
| Backend | Python / Django |
| Base de données | PostgreSQL |
| Frontend | HTML5 / CSS3 / JavaScript |
| PDF | ReportLab |
| Hébergement | Cloud sécurisé |

---

# III. CONFORMITÉ LÉGALE

## 3.1 Textes de référence

Le système a été développé en conformité avec :

1. **Code Général des Impôts (CGI) 2022**
   - Barème RTS (Art. XX)
   - Versement Forfaitaire (Art. XX)
   - Taxe d'Apprentissage (Art. XX)

2. **Code du Travail**
   - Heures supplémentaires (Art. 221)
   - Congés payés (Art. 153)
   - Indemnités de licenciement

3. **Règlements CNSS**
   - Taux de cotisation
   - Plafond et plancher
   - Déclarations

## 3.2 Barème RTS implémenté

| Tranche | Revenus mensuels (GNF) | Taux |
|---------|------------------------|------|
| 1 | 0 - 1 000 000 | 0% |
| 2 | 1 000 001 - 3 000 000 | 5% |
| 3 | 3 000 001 - 5 000 000 | 8% |
| 4 | 5 000 001 - 10 000 000 | 10% |
| 5 | 10 000 001 - 20 000 000 | 15% |
| 6 | Au-delà de 20 000 000 | 20% |

## 3.3 Taux de cotisations implémentés

| Cotisation | Taux | Base de calcul |
|------------|------|----------------|
| CNSS Salarié | 5% | Salaire plafonné |
| CNSS Employeur | 18% | Salaire plafonné |
| VF | 6% | Salaire brut |
| TA | 1,5% | Salaire brut |
| ONFPP | 1,5% | Salaire brut |

## 3.4 Plafonds et seuils

| Paramètre | Valeur |
|-----------|--------|
| SMIG | 550 000 GNF |
| Plancher CNSS | 550 000 GNF |
| Plafond CNSS | 2 500 000 GNF |
| Exonération stagiaires | 1 200 000 GNF/mois |
| Plafond indemnités | 25% du brut |

---

# IV. FONCTIONNEMENT DU CALCUL

## 4.1 Processus de calcul

```
1. Collecte des éléments de salaire
2. Calcul du salaire brut
3. Vérification plafond 25% indemnités
4. Calcul CNSS (avec plafond/plancher)
5. Calcul base imposable RTS
6. Application barème progressif 6 tranches
7. Calcul charges patronales
8. Génération bulletin de paie
```

## 4.2 Formules utilisées

### CNSS
```
Assiette = MIN(MAX(Brut, Plancher), Plafond)
CNSS Salarié = Assiette × 5%
CNSS Employeur = Assiette × 18%
```

### RTS
```
Base imposable = Brut - CNSS Salarié + Excédent indemnités
RTS = Σ (Montant tranche × Taux tranche)
```

### Charges patronales
```
VF = Brut × 6%
TA = Brut × 1,5%
Total = CNSS Employeur + VF + TA
```

---

# V. SÉCURITÉ ET TRAÇABILITÉ

## 5.1 Mesures de sécurité

| Mesure | Description |
|--------|-------------|
| Authentification | Login sécurisé, mots de passe chiffrés |
| Autorisation | Rôles et permissions par module |
| Chiffrement | HTTPS, données sensibles chiffrées |
| Sauvegarde | Automatique quotidienne |

## 5.2 Traçabilité

| Élément tracé | Information enregistrée |
|---------------|-------------------------|
| Connexions | Utilisateur, date, heure, IP |
| Modifications | Auteur, date, valeur avant/après |
| Bulletins | Numéro unique, horodatage |
| Exports | Date, utilisateur, type |

## 5.3 Conservation des données

| Type de données | Durée de conservation |
|-----------------|----------------------|
| Bulletins de paie | 10 ans |
| Déclarations | 10 ans |
| Journaux d'audit | 5 ans |

---

# VI. PIÈCES JOINTES

## Documents fournis

1. ☐ Rapport d'audit de conformité
2. ☐ Manuel d'utilisation
3. ☐ Exercice de calcul détaillé
4. ☐ Captures d'écran du système
5. ☐ Certificat d'hébergement sécurisé
6. ☐ Attestation de l'éditeur

---

# VII. ENGAGEMENT

Je soussigné, [Nom du responsable], en qualité de [Fonction], certifie que :

1. Les informations contenues dans ce dossier sont exactes et vérifiables.

2. Le système GuineeRH.space est conforme aux dispositions du Code Général des Impôts 2022 et du Code du Travail guinéen.

3. Toute modification législative sera intégrée dans un délai de 30 jours suivant sa publication officielle.

4. L'éditeur s'engage à collaborer avec les autorités compétentes pour tout contrôle ou audit.

**Fait à** : [Ville], le [Date]

**Signature** : ________________________

**Cachet** : 

---

# VIII. RÉSERVÉ À L'ADMINISTRATION

## Décision

☐ Agrément accordé  
☐ Agrément refusé  
☐ Demande de compléments  

**Motif** : _________________________________

**Date de décision** : ____________________

**Numéro d'agrément** : __________________

**Signature autorité** : ___________________

---

*Document généré par GuineeRH.space - Version 3.0*
