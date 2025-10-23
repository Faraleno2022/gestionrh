-- ============================================
-- DONNÉES D'INITIALISATION - RH GUINÉE
-- ============================================

-- ============================================
-- 1. PROFILS UTILISATEURS
-- ============================================

INSERT INTO profils_utilisateurs (nom_profil, description, niveau_acces, actif) VALUES
('Consultation', 'Accès en lecture seule aux informations', 1, TRUE),
('Opérateur RH', 'Saisie et modification des données RH courantes', 2, TRUE),
('Manager', 'Gestion d''équipe, validation congés et pointages', 3, TRUE),
('Responsable RH', 'Gestion complète RH, paie et déclarations', 4, TRUE),
('Administrateur', 'Accès complet au système et configuration', 5, TRUE)
ON CONFLICT (nom_profil) DO NOTHING;

-- ============================================
-- 2. PARAMÈTRES DE PAIE GUINÉE (2025)
-- ============================================

INSERT INTO parametres_paie (code_parametre, libelle_parametre, valeur_numerique, type_parametre, categorie, unite, actif, date_debut_validite) VALUES
-- Salaires et plafonds
('SMIG', 'Salaire Minimum Interprofessionnel Garanti', 440000, 'Numérique', 'Général', 'GNF', TRUE, '2025-01-01'),
('PLAFOND_CNSS', 'Plafond de cotisation CNSS', 3000000, 'Numérique', 'CNSS', 'GNF', TRUE, '2025-01-01'),
('PLAFOND_INAM', 'Plafond de cotisation INAM', 3000000, 'Numérique', 'INAM', 'GNF', TRUE, '2025-01-01'),

-- Taux de cotisations sociales
('TAUX_CNSS_EMPLOYE', 'Taux de cotisation CNSS employé', 5.00, 'Numérique', 'CNSS', '%', TRUE, '2025-01-01'),
('TAUX_CNSS_EMPLOYEUR', 'Taux de cotisation CNSS employeur', 18.00, 'Numérique', 'CNSS', '%', TRUE, '2025-01-01'),
('TAUX_INAM', 'Taux de cotisation INAM', 2.50, 'Numérique', 'INAM', '%', TRUE, '2025-01-01'),

-- IRG
('ABATTEMENT_IRG', 'Abattement forfaitaire IRG', 20.00, 'Numérique', 'IRG', '%', TRUE, '2025-01-01'),
('PLAFOND_ABATTEMENT_IRG', 'Plafond abattement IRG', 300000, 'Numérique', 'IRG', 'GNF', TRUE, '2025-01-01'),

-- Temps de travail
('HEURES_MOIS_STANDARD', 'Nombre d''heures standard par mois', 173.33, 'Numérique', 'Général', 'Heures', TRUE, '2025-01-01'),
('JOURS_MOIS_STANDARD', 'Nombre de jours standard par mois', 22, 'Numérique', 'Général', 'Jours', TRUE, '2025-01-01'),
('JOURS_CONGES_ANNUELS', 'Nombre de jours de congés annuels', 26, 'Numérique', 'Général', 'Jours', TRUE, '2025-01-01'),
('HEURES_SEMAINE', 'Durée légale hebdomadaire', 40, 'Numérique', 'Général', 'Heures', TRUE, '2025-01-01'),

-- Heures supplémentaires
('TAUX_HS_NORMALE', 'Majoration heures supplémentaires normales', 40.00, 'Numérique', 'Général', '%', TRUE, '2025-01-01'),
('TAUX_HS_NUIT', 'Majoration heures supplémentaires nuit', 60.00, 'Numérique', 'Général', '%', TRUE, '2025-01-01'),
('TAUX_HS_DIMANCHE', 'Majoration heures supplémentaires dimanche', 60.00, 'Numérique', 'Général', '%', TRUE, '2025-01-01'),
('TAUX_HS_FERIE', 'Majoration heures supplémentaires jour férié', 100.00, 'Numérique', 'Général', '%', TRUE, '2025-01-01')
ON CONFLICT (code_parametre) DO NOTHING;

-- ============================================
-- 3. TRANCHES IRG GUINÉE (2025)
-- ============================================

INSERT INTO tranches_irg (numero_tranche, borne_inferieure, borne_superieure, taux_irg, annee_validite, actif, date_debut_validite) VALUES
(1, 0, 1000000, 0.00, 2025, TRUE, '2025-01-01'),
(2, 1000001, 3000000, 5.00, 2025, TRUE, '2025-01-01'),
(3, 3000001, 6000000, 10.00, 2025, TRUE, '2025-01-01'),
(4, 6000001, 12000000, 15.00, 2025, TRUE, '2025-01-01'),
(5, 12000001, 25000000, 20.00, 2025, TRUE, '2025-01-01'),
(6, 25000001, NULL, 25.00, 2025, TRUE, '2025-01-01');

-- ============================================
-- 4. JOURS FÉRIÉS GUINÉE 2025
-- ============================================

INSERT INTO calendrier_jours_feries (libelle, date_jour_ferie, annee, type_ferie, recurrent) VALUES
('Jour de l''An', '2025-01-01', 2025, 'National', TRUE),
('Lundi de Pâques', '2025-04-21', 2025, 'Religieux', FALSE),
('Fête du Travail', '2025-05-01', 2025, 'National', TRUE),
('Aïd el-Fitr (fin Ramadan)', '2025-03-31', 2025, 'Religieux', FALSE),
('Aïd el-Kebir (Tabaski)', '2025-06-07', 2025, 'Religieux', FALSE),
('Maouloud (Naissance du Prophète)', '2025-09-05', 2025, 'Religieux', FALSE),
('Fête de l''Indépendance', '2025-10-02', 2025, 'National', TRUE),
('Noël', '2025-12-25', 2025, 'Religieux', TRUE);

-- ============================================
-- 5. RUBRIQUES DE PAIE STANDARD
-- ============================================

INSERT INTO rubriques_paie (code_rubrique, libelle_rubrique, type_rubrique, nature_rubrique, base_calcul, taux_rubrique, montant_fixe, ordre_calcul, soumis_cnss, soumis_irg, soumis_inam, ordre_affichage, actif, affichage_bulletin) VALUES
-- GAINS (100-199)
('SAL_BASE', 'Salaire de Base', 'Gain', 'Salaire_base', 'Fixe', NULL, NULL, 100, TRUE, TRUE, FALSE, 1, TRUE, TRUE),
('PRIME_ANC', 'Prime d''Ancienneté', 'Gain', 'Prime', 'Base', NULL, NULL, 110, TRUE, TRUE, FALSE, 2, TRUE, TRUE),
('PRIME_FONC', 'Prime de Fonction', 'Gain', 'Prime', 'Fixe', NULL, NULL, 120, TRUE, TRUE, FALSE, 3, TRUE, TRUE),
('PRIME_REND', 'Prime de Rendement', 'Gain', 'Prime', 'Fixe', NULL, NULL, 130, TRUE, TRUE, FALSE, 4, TRUE, TRUE),
('PRIME_RESP', 'Prime de Responsabilité', 'Gain', 'Prime', 'Fixe', NULL, NULL, 140, TRUE, TRUE, FALSE, 5, TRUE, TRUE),
('IND_TRANS', 'Indemnité de Transport', 'Gain', 'Indemnité', 'Fixe', NULL, NULL, 150, TRUE, TRUE, FALSE, 6, TRUE, TRUE),
('IND_LOG', 'Indemnité de Logement', 'Gain', 'Indemnité', 'Fixe', NULL, NULL, 160, TRUE, TRUE, FALSE, 7, TRUE, TRUE),
('IND_NOUR', 'Indemnité de Nourriture', 'Gain', 'Indemnité', 'Fixe', NULL, NULL, 170, TRUE, TRUE, FALSE, 8, TRUE, TRUE),
('HS_NORM', 'Heures Supplémentaires Normales', 'Gain', 'Heures_sup', 'Base', 1.40, NULL, 180, TRUE, TRUE, FALSE, 9, TRUE, TRUE),
('HS_NUIT', 'Heures Supplémentaires Nuit', 'Gain', 'Heures_sup', 'Base', 1.60, NULL, 190, TRUE, TRUE, FALSE, 10, TRUE, TRUE),
('HS_DIM', 'Heures Supplémentaires Dimanche', 'Gain', 'Heures_sup', 'Base', 1.60, NULL, 195, TRUE, TRUE, FALSE, 11, TRUE, TRUE),
('HS_FERIE', 'Heures Supplémentaires Jour Férié', 'Gain', 'Heures_sup', 'Base', 2.00, NULL, 198, TRUE, TRUE, FALSE, 12, TRUE, TRUE),
('AVANTAGE_NAT', 'Avantages en Nature', 'Gain', 'Avantage', 'Fixe', NULL, NULL, 199, TRUE, TRUE, FALSE, 13, TRUE, TRUE),

-- RETENUES SOCIALES (200-299)
('CNSS_EMP', 'Cotisation CNSS Employé', 'Retenue', 'CNSS', 'Base', 5.00, NULL, 200, FALSE, FALSE, FALSE, 20, TRUE, TRUE),
('INAM_EMP', 'Cotisation INAM Employé', 'Retenue', 'INAM', 'Base', 2.50, NULL, 210, FALSE, FALSE, FALSE, 21, TRUE, TRUE),
('IRG', 'Impôt sur Revenu (IRG)', 'Retenue', 'IRG', 'Base', NULL, NULL, 220, FALSE, FALSE, FALSE, 22, TRUE, TRUE),

-- COTISATIONS PATRONALES (300-399)
('CNSS_PAT', 'Cotisation CNSS Employeur', 'Cotisation', 'CNSS', 'Base', 18.00, NULL, 300, FALSE, FALSE, FALSE, 30, TRUE, FALSE),

-- AUTRES RETENUES (400-499)
('ACOMPTE', 'Acompte sur Salaire', 'Retenue', 'Acompte', 'Fixe', NULL, NULL, 400, FALSE, FALSE, FALSE, 40, TRUE, TRUE),
('PRET', 'Remboursement Prêt', 'Retenue', 'Prêt', 'Fixe', NULL, NULL, 410, FALSE, FALSE, FALSE, 41, TRUE, TRUE),
('SANCTION', 'Retenue Sanction', 'Retenue', 'Sanction', 'Fixe', NULL, NULL, 420, FALSE, FALSE, FALSE, 42, TRUE, TRUE),
('SAISIE_ARR', 'Saisie-Arrêt', 'Retenue', 'Juridique', 'Fixe', NULL, NULL, 430, FALSE, FALSE, FALSE, 43, TRUE, TRUE),
('ABSENCE', 'Retenue Absence', 'Retenue', 'Absence', 'Base', NULL, NULL, 440, FALSE, FALSE, FALSE, 44, TRUE, TRUE),

-- LIGNES DE CALCUL (500-599)
('BRUT', 'Salaire Brut', 'Information', 'Calcul', NULL, NULL, NULL, 500, FALSE, FALSE, FALSE, 50, TRUE, TRUE),
('BASE_CNSS', 'Base de Cotisation CNSS', 'Information', 'Calcul', NULL, NULL, NULL, 510, FALSE, FALSE, FALSE, 51, TRUE, TRUE),
('BASE_IRG', 'Base Imposable IRG', 'Information', 'Calcul', NULL, NULL, NULL, 520, FALSE, FALSE, FALSE, 52, TRUE, TRUE),
('NET_IMP', 'Net Imposable', 'Information', 'Calcul', NULL, NULL, NULL, 530, FALSE, FALSE, FALSE, 53, TRUE, TRUE),
('NET', 'Net à Payer', 'Information', 'Calcul', NULL, NULL, NULL, 600, FALSE, FALSE, FALSE, 60, TRUE, TRUE)
ON CONFLICT (code_rubrique) DO NOTHING;

-- ============================================
-- 6. HORAIRES DE TRAVAIL
-- ============================================

INSERT INTO horaires_travail (code_horaire, libelle_horaire, heure_debut, heure_fin, heure_pause_debut, heure_pause_fin, heures_jour, type_horaire, actif) VALUES
('NORMAL', 'Horaire Normal (8h-17h)', '08:00:00', '17:00:00', '12:00:00', '13:00:00', 8.00, 'Normal', TRUE),
('CONTINU', 'Horaire Continu (8h-16h)', '08:00:00', '16:00:00', NULL, NULL, 8.00, 'Normal', TRUE),
('MATIN', 'Équipe Matin (6h-14h)', '06:00:00', '14:00:00', '10:00:00', '10:30:00', 7.50, 'Équipe', TRUE),
('APREM', 'Équipe Après-midi (14h-22h)', '14:00:00', '22:00:00', '18:00:00', '18:30:00', 7.50, 'Équipe', TRUE),
('NUIT', 'Équipe Nuit (22h-6h)', '22:00:00', '06:00:00', '02:00:00', '02:30:00', 7.50, 'Nuit', TRUE),
('ADMIN', 'Horaire Administratif (7h30-15h30)', '07:30:00', '15:30:00', '12:00:00', '13:00:00', 8.00, 'Normal', TRUE)
ON CONFLICT (code_horaire) DO NOTHING;

-- ============================================
-- 7. TYPES DE PRÊTS
-- ============================================

INSERT INTO types_prets (code_type_pret, libelle_type_pret, montant_maximum, duree_maximum_mois, taux_interet, actif) VALUES
('PRET_PERS', 'Prêt Personnel', 5000000, 24, 5.00, TRUE),
('PRET_SCOL', 'Prêt Scolaire', 3000000, 12, 3.00, TRUE),
('PRET_LOG', 'Prêt Logement', 10000000, 36, 4.00, TRUE),
('PRET_SANTE', 'Prêt Santé', 2000000, 12, 2.00, TRUE),
('PRET_URGENCE', 'Prêt d''Urgence', 1000000, 6, 0.00, TRUE),
('PRET_EQUIP', 'Prêt Équipement', 4000000, 18, 4.50, TRUE)
ON CONFLICT (code_type_pret) DO NOTHING;

-- ============================================
-- 8. TYPES DE DÉPART
-- ============================================

INSERT INTO types_depart (code_type_depart, libelle_type_depart, categorie, calcul_indemnites, preavis_requis) VALUES
('DEM', 'Démission', 'Volontaire', TRUE, TRUE),
('LIC_ECO', 'Licenciement Économique', 'Involontaire', TRUE, TRUE),
('LIC_FAUTE', 'Licenciement pour Faute Grave', 'Involontaire', FALSE, FALSE),
('LIC_FAUTE_SIMPLE', 'Licenciement pour Faute Simple', 'Involontaire', TRUE, TRUE),
('FIN_CDD', 'Fin de Contrat CDD', 'Naturel', TRUE, FALSE),
('FIN_ESSAI', 'Fin de Période d''Essai', 'Naturel', FALSE, FALSE),
('RETRAITE', 'Départ à la Retraite', 'Naturel', TRUE, FALSE),
('RETRAITE_ANT', 'Retraite Anticipée', 'Volontaire', TRUE, FALSE),
('DECES', 'Décès', 'Naturel', FALSE, FALSE),
('MUT_CONV', 'Mutation Conventionnelle', 'Volontaire', FALSE, TRUE),
('ABANDON', 'Abandon de Poste', 'Involontaire', FALSE, FALSE),
('INAPTITUDE', 'Inaptitude Physique', 'Involontaire', TRUE, FALSE)
ON CONFLICT (code_type_depart) DO NOTHING;

-- ============================================
-- 9. TYPES DE SANCTIONS
-- ============================================

INSERT INTO types_sanctions (code_sanction, libelle_sanction, categorie, niveau_gravite, impact_paie, impact_carriere) VALUES
('AVERT_ORAL', 'Avertissement Oral', 'Avertissement', 1, FALSE, FALSE),
('AVERT_ECRIT', 'Avertissement Écrit', 'Avertissement', 2, FALSE, FALSE),
('BLAME', 'Blâme', 'Blâme', 3, FALSE, TRUE),
('MAP_1J', 'Mise à Pied 1 Jour', 'Mise_à_pied', 4, TRUE, TRUE),
('MAP_3J', 'Mise à Pied 3 Jours', 'Mise_à_pied', 5, TRUE, TRUE),
('MAP_8J', 'Mise à Pied 8 Jours', 'Mise_à_pied', 6, TRUE, TRUE),
('MAP_15J', 'Mise à Pied 15 Jours', 'Mise_à_pied', 7, TRUE, TRUE),
('RETRO', 'Rétrogradation', 'Rétrogradation', 8, TRUE, TRUE),
('MUT_SANC', 'Mutation Disciplinaire', 'Mutation', 8, FALSE, TRUE),
('LIC_FAUTE', 'Licenciement pour Faute', 'Licenciement', 10, TRUE, TRUE)
ON CONFLICT (code_sanction) DO NOTHING;

-- ============================================
-- 10. INDICATEURS RH
-- ============================================

INSERT INTO indicateurs_rh (code_indicateur, libelle_indicateur, categorie, type_calcul, unite_mesure, frequence_calcul, actif) VALUES
-- Effectif
('EFF_TOTAL', 'Effectif Total', 'Effectif', 'Comptage', 'Nombre', 'Mensuel', TRUE),
('EFF_HOMME', 'Effectif Hommes', 'Effectif', 'Comptage', 'Nombre', 'Mensuel', TRUE),
('EFF_FEMME', 'Effectif Femmes', 'Effectif', 'Comptage', 'Nombre', 'Mensuel', TRUE),
('EFF_CDI', 'Effectif CDI', 'Effectif', 'Comptage', 'Nombre', 'Mensuel', TRUE),
('EFF_CDD', 'Effectif CDD', 'Effectif', 'Comptage', 'Nombre', 'Mensuel', TRUE),
('AGE_MOYEN', 'Âge Moyen', 'Effectif', 'Moyenne', 'Années', 'Mensuel', TRUE),
('ANC_MOYENNE', 'Ancienneté Moyenne', 'Effectif', 'Moyenne', 'Années', 'Mensuel', TRUE),

-- Paie
('MASSE_SAL', 'Masse Salariale Brute', 'Paie', 'Somme', 'GNF', 'Mensuel', TRUE),
('MASSE_SAL_NET', 'Masse Salariale Nette', 'Paie', 'Somme', 'GNF', 'Mensuel', TRUE),
('SAL_MOYEN', 'Salaire Moyen Brut', 'Paie', 'Moyenne', 'GNF', 'Mensuel', TRUE),
('SAL_MEDIAN', 'Salaire Médian', 'Paie', 'Moyenne', 'GNF', 'Mensuel', TRUE),
('CHARGES_SOC', 'Total Charges Sociales', 'Paie', 'Somme', 'GNF', 'Mensuel', TRUE),
('COUT_TOTAL', 'Coût Total Employeur', 'Paie', 'Somme', 'GNF', 'Mensuel', TRUE),

-- Temps de travail
('TAUX_ABS', 'Taux d''Absentéisme', 'Temps', 'Ratio', '%', 'Mensuel', TRUE),
('HEURES_SUP', 'Total Heures Supplémentaires', 'Temps', 'Somme', 'Heures', 'Mensuel', TRUE),
('JOURS_CONGES', 'Jours de Congés Pris', 'Temps', 'Somme', 'Jours', 'Mensuel', TRUE),
('TAUX_PRESENCE', 'Taux de Présence', 'Temps', 'Ratio', '%', 'Mensuel', TRUE),

-- Turnover
('TAUX_TURN', 'Taux de Turnover', 'Turnover', 'Ratio', '%', 'Annuel', TRUE),
('NB_DEPARTS', 'Nombre de Départs', 'Turnover', 'Comptage', 'Nombre', 'Mensuel', TRUE),
('NB_RECRUT', 'Nombre de Recrutements', 'Turnover', 'Comptage', 'Nombre', 'Mensuel', TRUE),
('TAUX_DEMISSION', 'Taux de Démission', 'Turnover', 'Ratio', '%', 'Annuel', TRUE),

-- Formation
('HEURES_FORM', 'Total Heures de Formation', 'Formation', 'Somme', 'Heures', 'Annuel', TRUE),
('COUT_FORM', 'Coût Total Formation', 'Formation', 'Somme', 'GNF', 'Annuel', TRUE),
('NB_FORM', 'Nombre de Formations', 'Formation', 'Comptage', 'Nombre', 'Annuel', TRUE),
('TAUX_FORM', 'Taux de Formation', 'Formation', 'Ratio', '%', 'Annuel', TRUE)
ON CONFLICT (code_indicateur) DO NOTHING;

-- ============================================
-- 11. CONSTANTES DE CALCUL
-- ============================================

INSERT INTO constantes_calcul (code_constante, libelle_constante, valeur_fixe, type_constante, actif) VALUES
('NB_JOURS_AN', 'Nombre de jours par an', 365, 'Fixe', TRUE),
('NB_MOIS_AN', 'Nombre de mois par an', 12, 'Fixe', TRUE),
('NB_HEURES_JOUR', 'Nombre d''heures par jour', 8, 'Fixe', TRUE),
('NB_JOURS_SEMAINE', 'Nombre de jours par semaine', 5, 'Fixe', TRUE)
ON CONFLICT (code_constante) DO NOTHING;

-- ============================================
-- 12. VARIABLES DE PAIE
-- ============================================

INSERT INTO variables_paie (code_variable, libelle_variable, type_variable, valeur_defaut, portee) VALUES
('NB_JOURS_TRAVAILLES', 'Nombre de jours travaillés', 'Numérique', '22', 'Employé'),
('NB_HEURES_SUP', 'Nombre d''heures supplémentaires', 'Numérique', '0', 'Employé'),
('NB_JOURS_ABSENCE', 'Nombre de jours d''absence', 'Numérique', '0', 'Employé'),
('TAUX_ACTIVITE', 'Taux d''activité', 'Numérique', '100', 'Employé'),
('PRIME_VARIABLE', 'Prime variable du mois', 'Numérique', '0', 'Employé')
ON CONFLICT (code_variable) DO NOTHING;

-- ============================================
-- FIN DU SCRIPT D'INITIALISATION
-- ============================================

-- Affichage du résumé
SELECT 'Initialisation terminée avec succès!' AS statut;
SELECT 'Profils utilisateurs: ' || COUNT(*) FROM profils_utilisateurs;
SELECT 'Paramètres de paie: ' || COUNT(*) FROM parametres_paie;
SELECT 'Tranches IRG: ' || COUNT(*) FROM tranches_irg;
SELECT 'Jours fériés 2025: ' || COUNT(*) FROM calendrier_jours_feries WHERE annee = 2025;
SELECT 'Rubriques de paie: ' || COUNT(*) FROM rubriques_paie;
SELECT 'Horaires de travail: ' || COUNT(*) FROM horaires_travail;
SELECT 'Types de prêts: ' || COUNT(*) FROM types_prets;
SELECT 'Types de départ: ' || COUNT(*) FROM types_depart;
SELECT 'Types de sanctions: ' || COUNT(*) FROM types_sanctions;
SELECT 'Indicateurs RH: ' || COUNT(*) FROM indicateurs_rh;
