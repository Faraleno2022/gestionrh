-- ============================================
-- VUES ET INDEX - GESTIONNAIRE RH GUINÉE
-- ============================================

-- ============================================
-- VUES PRINCIPALES
-- ============================================

-- Vue des employés actifs avec informations complètes
CREATE OR REPLACE VIEW v_employes_actifs AS
SELECT 
    e.id_employe,
    e.matricule,
    e.civilite,
    e.nom,
    e.prenoms,
    e.nom || ' ' || e.prenoms AS nom_complet,
    e.sexe,
    e.date_naissance,
    DATE_PART('year', AGE(e.date_naissance)) AS age,
    e.situation_matrimoniale,
    e.nombre_enfants,
    e.num_cnss_individuel,
    e.telephone_principal,
    e.email_professionnel,
    e.date_embauche,
    DATE_PART('year', AGE(e.date_embauche)) AS anciennete_annees,
    DATE_PART('month', AGE(e.date_embauche)) AS anciennete_mois,
    e.type_contrat,
    e.statut_employe,
    soc.raison_sociale,
    et.nom_etablissement,
    et.ville AS ville_etablissement,
    s.nom_service,
    s.code_service,
    p.intitule_poste,
    p.categorie_professionnelle,
    p.classification,
    sup.nom || ' ' || sup.prenoms AS superieur_hierarchique,
    g.salaire_base,
    g.salaire_brut_mensuel
FROM employes e
LEFT JOIN etablissements et ON e.id_etablissement = et.id_etablissement
LEFT JOIN societe soc ON et.id_societe = soc.id_societe
LEFT JOIN services s ON e.id_service = s.id_service
LEFT JOIN postes p ON e.id_poste = p.id_poste
LEFT JOIN employes sup ON e.id_superieur_hierarchique = sup.id_employe
LEFT JOIN LATERAL (
    SELECT salaire_base, salaire_brut_mensuel
    FROM grilles_salariales
    WHERE id_employe = e.id_employe AND actif = TRUE
    ORDER BY date_effet DESC
    LIMIT 1
) g ON TRUE
WHERE e.statut_employe = 'Actif';

-- Vue livre de paie mensuel
CREATE OR REPLACE VIEW v_livre_paie AS
SELECT 
    pp.annee,
    pp.mois,
    pp.libelle AS periode,
    pp.date_paiement,
    e.matricule,
    e.nom || ' ' || e.prenoms AS nom_complet,
    e.num_cnss_individuel,
    s.nom_service,
    p.intitule_poste,
    p.categorie_professionnelle,
    bp.nombre_jours_payes,
    bp.nombre_heures_normales,
    bp.nombre_heures_supplementaires,
    bp.salaire_brut,
    bp.base_cnss,
    bp.cnss_employe,
    bp.inam_employe,
    bp.base_irg,
    bp.irg,
    bp.total_retenues,
    bp.net_a_payer,
    bp.cnss_employeur,
    bp.total_charges_patronales,
    bp.cout_total_employeur,
    bp.statut_bulletin,
    bp.mode_paiement
FROM bulletins_paie bp
INNER JOIN employes e ON bp.id_employe = e.id_employe
INNER JOIN periodes_paie pp ON bp.id_periode = pp.id_periode
LEFT JOIN services s ON e.id_service = s.id_service
LEFT JOIN postes p ON e.id_poste = p.id_poste
ORDER BY pp.annee DESC, pp.mois DESC, e.matricule;

-- Vue pyramide des âges
CREATE OR REPLACE VIEW v_pyramide_ages AS
SELECT 
    CASE 
        WHEN DATE_PART('year', AGE(date_naissance)) < 25 THEN '< 25 ans'
        WHEN DATE_PART('year', AGE(date_naissance)) BETWEEN 25 AND 34 THEN '25-34 ans'
        WHEN DATE_PART('year', AGE(date_naissance)) BETWEEN 35 AND 44 THEN '35-44 ans'
        WHEN DATE_PART('year', AGE(date_naissance)) BETWEEN 45 AND 54 THEN '45-54 ans'
        ELSE '55 ans et +'
    END AS tranche_age,
    sexe,
    COUNT(*) AS effectif,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pourcentage
FROM employes
WHERE statut_employe = 'Actif'
GROUP BY tranche_age, sexe
ORDER BY tranche_age, sexe;

-- Vue effectif par service
CREATE OR REPLACE VIEW v_effectif_par_service AS
SELECT 
    et.nom_etablissement,
    s.code_service,
    s.nom_service,
    COUNT(e.id_employe) AS effectif_total,
    COUNT(CASE WHEN e.sexe = 'M' THEN 1 END) AS hommes,
    COUNT(CASE WHEN e.sexe = 'F' THEN 1 END) AS femmes,
    COUNT(CASE WHEN e.type_contrat = 'CDI' THEN 1 END) AS cdi,
    COUNT(CASE WHEN e.type_contrat = 'CDD' THEN 1 END) AS cdd,
    ROUND(AVG(DATE_PART('year', AGE(e.date_naissance))), 1) AS age_moyen,
    ROUND(AVG(DATE_PART('year', AGE(e.date_embauche))), 1) AS anciennete_moyenne,
    resp.nom || ' ' || resp.prenoms AS responsable_service
FROM services s
LEFT JOIN etablissements et ON s.id_etablissement = et.id_etablissement
LEFT JOIN employes e ON s.id_service = e.id_service AND e.statut_employe = 'Actif'
LEFT JOIN employes resp ON s.responsable_service = resp.id_employe
GROUP BY et.nom_etablissement, s.id_service, s.code_service, s.nom_service, resp.nom, resp.prenoms
ORDER BY et.nom_etablissement, s.nom_service;

-- Vue effectif par catégorie professionnelle
CREATE OR REPLACE VIEW v_effectif_par_categorie AS
SELECT 
    p.categorie_professionnelle,
    COUNT(e.id_employe) AS effectif,
    COUNT(CASE WHEN e.sexe = 'M' THEN 1 END) AS hommes,
    COUNT(CASE WHEN e.sexe = 'F' THEN 1 END) AS femmes,
    ROUND(AVG(g.salaire_brut_mensuel), 0) AS salaire_moyen,
    MIN(g.salaire_brut_mensuel) AS salaire_min,
    MAX(g.salaire_brut_mensuel) AS salaire_max
FROM employes e
INNER JOIN postes p ON e.id_poste = p.id_poste
LEFT JOIN LATERAL (
    SELECT salaire_brut_mensuel
    FROM grilles_salariales
    WHERE id_employe = e.id_employe AND actif = TRUE
    ORDER BY date_effet DESC
    LIMIT 1
) g ON TRUE
WHERE e.statut_employe = 'Actif'
GROUP BY p.categorie_professionnelle
ORDER BY effectif DESC;

-- Vue soldes de congés
CREATE OR REPLACE VIEW v_soldes_conges AS
SELECT 
    e.matricule,
    e.nom || ' ' || e.prenoms AS nom_complet,
    s.nom_service,
    sc.annee,
    sc.conges_acquis,
    sc.conges_pris,
    sc.conges_restants,
    sc.conges_reports,
    sc.date_mise_a_jour,
    CASE 
        WHEN sc.conges_restants < 5 THEN 'Critique'
        WHEN sc.conges_restants < 10 THEN 'Attention'
        ELSE 'Normal'
    END AS statut_solde
FROM soldes_conges sc
INNER JOIN employes e ON sc.id_employe = e.id_employe
LEFT JOIN services s ON e.id_service = s.id_service
WHERE e.statut_employe = 'Actif' AND sc.annee = DATE_PART('year', CURRENT_DATE)
ORDER BY sc.conges_restants ASC;

-- Vue congés en cours et à venir
CREATE OR REPLACE VIEW v_conges_en_cours AS
SELECT 
    c.id_conge,
    e.matricule,
    e.nom || ' ' || e.prenoms AS nom_complet,
    s.nom_service,
    c.type_conge,
    c.date_debut,
    c.date_fin,
    c.nombre_jours,
    c.statut_demande,
    c.date_demande,
    app.nom || ' ' || app.prenoms AS approbateur,
    c.date_approbation,
    remp.nom || ' ' || remp.prenoms AS remplacant,
    CASE 
        WHEN c.date_debut <= CURRENT_DATE AND c.date_fin >= CURRENT_DATE THEN 'En cours'
        WHEN c.date_debut > CURRENT_DATE THEN 'À venir'
        ELSE 'Terminé'
    END AS statut_periode
FROM conges c
INNER JOIN employes e ON c.id_employe = e.id_employe
LEFT JOIN services s ON e.id_service = s.id_service
LEFT JOIN employes app ON c.approbateur = app.id_employe
LEFT JOIN employes remp ON c.remplacant = remp.id_employe
WHERE c.statut_demande = 'Approuvé'
  AND c.date_fin >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY c.date_debut;

-- Vue prêts en cours
CREATE OR REPLACE VIEW v_prets_en_cours AS
SELECT 
    pr.id_pret,
    pr.numero_pret,
    e.matricule,
    e.nom || ' ' || e.prenoms AS nom_complet,
    s.nom_service,
    tp.libelle_type_pret,
    pr.montant_pret,
    pr.taux_interet,
    pr.duree_mois,
    pr.montant_mensuel,
    pr.date_octroi,
    pr.date_premier_remboursement,
    pr.montant_rembourse,
    pr.montant_restant,
    pr.nombre_echeances_payees,
    pr.duree_mois - pr.nombre_echeances_payees AS echeances_restantes,
    ROUND((pr.montant_rembourse * 100.0 / pr.montant_pret), 2) AS pourcentage_rembourse
FROM prets pr
INNER JOIN employes e ON pr.id_employe = e.id_employe
LEFT JOIN services s ON e.id_service = s.id_service
INNER JOIN types_prets tp ON pr.id_type_pret = tp.id_type_pret
WHERE pr.statut_pret = 'Actif'
ORDER BY pr.date_octroi DESC;

-- Vue absences du mois
CREATE OR REPLACE VIEW v_absences_mois_courant AS
SELECT 
    a.id_absence,
    e.matricule,
    e.nom || ' ' || e.prenoms AS nom_complet,
    s.nom_service,
    p.intitule_poste,
    a.date_absence,
    a.type_absence,
    a.duree_jours,
    a.justifie,
    a.impact_paie,
    a.taux_maintien_salaire
FROM absences a
INNER JOIN employes e ON a.id_employe = e.id_employe
LEFT JOIN services s ON e.id_service = s.id_service
LEFT JOIN postes p ON e.id_poste = p.id_poste
WHERE DATE_PART('year', a.date_absence) = DATE_PART('year', CURRENT_DATE)
  AND DATE_PART('month', a.date_absence) = DATE_PART('month', CURRENT_DATE)
ORDER BY a.date_absence DESC, e.nom;

-- Vue contrats arrivant à échéance
CREATE OR REPLACE VIEW v_contrats_echeance AS
SELECT 
    ce.id_contrat,
    e.matricule,
    e.nom || ' ' || e.prenoms AS nom_complet,
    s.nom_service,
    p.intitule_poste,
    ce.type_contrat,
    ce.date_debut,
    ce.date_fin,
    ce.date_fin_essai,
    ce.statut_contrat,
    ce.renouvellements,
    CURRENT_DATE AS date_jour,
    ce.date_fin - CURRENT_DATE AS jours_restants,
    CASE 
        WHEN ce.date_fin - CURRENT_DATE <= 30 THEN 'Urgent'
        WHEN ce.date_fin - CURRENT_DATE <= 60 THEN 'Attention'
        ELSE 'Normal'
    END AS niveau_alerte
FROM contrats_employes ce
INNER JOIN employes e ON ce.id_employe = e.id_employe
LEFT JOIN services s ON e.id_service = s.id_service
LEFT JOIN postes p ON e.id_poste = p.id_poste
WHERE ce.statut_contrat = 'En cours'
  AND ce.date_fin IS NOT NULL
  AND ce.date_fin <= CURRENT_DATE + INTERVAL '90 days'
  AND e.statut_employe = 'Actif'
ORDER BY ce.date_fin ASC;

-- Vue statistiques paie mensuelle
CREATE OR REPLACE VIEW v_stats_paie_mensuelle AS
SELECT 
    pp.annee,
    pp.mois,
    pp.libelle AS periode,
    COUNT(bp.id_bulletin) AS nombre_bulletins,
    SUM(bp.salaire_brut) AS masse_salariale_brute,
    SUM(bp.net_a_payer) AS masse_salariale_nette,
    SUM(bp.cnss_employe) AS total_cnss_employe,
    SUM(bp.cnss_employeur) AS total_cnss_employeur,
    SUM(bp.inam_employe) AS total_inam,
    SUM(bp.irg) AS total_irg,
    SUM(bp.cout_total_employeur) AS cout_total,
    ROUND(AVG(bp.salaire_brut), 0) AS salaire_brut_moyen,
    ROUND(AVG(bp.net_a_payer), 0) AS salaire_net_moyen,
    pp.statut_periode
FROM periodes_paie pp
LEFT JOIN bulletins_paie bp ON pp.id_periode = bp.id_periode
GROUP BY pp.id_periode, pp.annee, pp.mois, pp.libelle, pp.statut_periode
ORDER BY pp.annee DESC, pp.mois DESC;

-- Vue turnover annuel
CREATE OR REPLACE VIEW v_turnover_annuel AS
SELECT 
    DATE_PART('year', d.date_depart_effectif) AS annee,
    COUNT(DISTINCT d.id_employe) AS nombre_departs,
    COUNT(DISTINCT CASE WHEN td.categorie = 'Volontaire' THEN d.id_employe END) AS departs_volontaires,
    COUNT(DISTINCT CASE WHEN td.categorie = 'Involontaire' THEN d.id_employe END) AS departs_involontaires,
    COUNT(DISTINCT CASE WHEN td.code_type_depart = 'DEM' THEN d.id_employe END) AS demissions,
    COUNT(DISTINCT CASE WHEN td.code_type_depart LIKE 'LIC%' THEN d.id_employe END) AS licenciements,
    COUNT(DISTINCT CASE WHEN td.code_type_depart = 'RETRAITE' THEN d.id_employe END) AS retraites,
    (SELECT COUNT(*) FROM employes WHERE statut_employe = 'Actif') AS effectif_actuel,
    ROUND(COUNT(DISTINCT d.id_employe) * 100.0 / NULLIF((SELECT COUNT(*) FROM employes WHERE statut_employe = 'Actif'), 0), 2) AS taux_turnover
FROM departs_employes d
INNER JOIN types_depart td ON d.id_type_depart = td.id_type_depart
GROUP BY DATE_PART('year', d.date_depart_effectif)
ORDER BY annee DESC;

-- ============================================
-- INDEX POUR OPTIMISATION DES PERFORMANCES
-- ============================================

-- Index sur table employes
CREATE INDEX IF NOT EXISTS idx_employes_matricule ON employes(matricule);
CREATE INDEX IF NOT EXISTS idx_employes_statut ON employes(statut_employe);
CREATE INDEX IF NOT EXISTS idx_employes_service ON employes(id_service);
CREATE INDEX IF NOT EXISTS idx_employes_etablissement ON employes(id_etablissement);
CREATE INDEX IF NOT EXISTS idx_employes_poste ON employes(id_poste);
CREATE INDEX IF NOT EXISTS idx_employes_cnss ON employes(num_cnss_individuel);
CREATE INDEX IF NOT EXISTS idx_employes_nom ON employes(nom, prenoms);
CREATE INDEX IF NOT EXISTS idx_employes_date_embauche ON employes(date_embauche);

-- Index sur table bulletins_paie
CREATE INDEX IF NOT EXISTS idx_bulletins_employe ON bulletins_paie(id_employe);
CREATE INDEX IF NOT EXISTS idx_bulletins_periode ON bulletins_paie(id_periode);
CREATE INDEX IF NOT EXISTS idx_bulletins_statut ON bulletins_paie(statut_bulletin);
CREATE INDEX IF NOT EXISTS idx_bulletins_annee_mois ON bulletins_paie(annee_paie, mois_paie);
CREATE INDEX IF NOT EXISTS idx_bulletins_date_calcul ON bulletins_paie(date_calcul);

-- Index sur table pointages
CREATE INDEX IF NOT EXISTS idx_pointages_employe ON pointages(id_employe);
CREATE INDEX IF NOT EXISTS idx_pointages_date ON pointages(date_pointage);
CREATE INDEX IF NOT EXISTS idx_pointages_employe_date ON pointages(id_employe, date_pointage);
CREATE INDEX IF NOT EXISTS idx_pointages_statut ON pointages(statut_pointage);
CREATE INDEX IF NOT EXISTS idx_pointages_valide ON pointages(valide);

-- Index sur table conges
CREATE INDEX IF NOT EXISTS idx_conges_employe ON conges(id_employe);
CREATE INDEX IF NOT EXISTS idx_conges_statut ON conges(statut_demande);
CREATE INDEX IF NOT EXISTS idx_conges_dates ON conges(date_debut, date_fin);
CREATE INDEX IF NOT EXISTS idx_conges_type ON conges(type_conge);
CREATE INDEX IF NOT EXISTS idx_conges_annee ON conges(annee_reference);

-- Index sur table absences
CREATE INDEX IF NOT EXISTS idx_absences_employe ON absences(id_employe);
CREATE INDEX IF NOT EXISTS idx_absences_date ON absences(date_absence);
CREATE INDEX IF NOT EXISTS idx_absences_type ON absences(type_absence);

-- Index sur table prets
CREATE INDEX IF NOT EXISTS idx_prets_employe ON prets(id_employe);
CREATE INDEX IF NOT EXISTS idx_prets_statut ON prets(statut_pret);
CREATE INDEX IF NOT EXISTS idx_prets_numero ON prets(numero_pret);

-- Index sur table acomptes
CREATE INDEX IF NOT EXISTS idx_acomptes_employe ON acomptes(id_employe);
CREATE INDEX IF NOT EXISTS idx_acomptes_statut ON acomptes(statut_acompte);
CREATE INDEX IF NOT EXISTS idx_acomptes_date ON acomptes(date_demande);

-- Index sur table logs_activite
CREATE INDEX IF NOT EXISTS idx_logs_utilisateur ON logs_activite(id_utilisateur);
CREATE INDEX IF NOT EXISTS idx_logs_date ON logs_activite(date_action);
CREATE INDEX IF NOT EXISTS idx_logs_module ON logs_activite(module);
CREATE INDEX IF NOT EXISTS idx_logs_action ON logs_activite(action);

-- Index sur table contrats_employes
CREATE INDEX IF NOT EXISTS idx_contrats_employe ON contrats_employes(id_employe);
CREATE INDEX IF NOT EXISTS idx_contrats_statut ON contrats_employes(statut_contrat);
CREATE INDEX IF NOT EXISTS idx_contrats_dates ON contrats_employes(date_debut, date_fin);

-- Index sur table formations_employes
CREATE INDEX IF NOT EXISTS idx_formations_employe ON formations_employes(id_employe);
CREATE INDEX IF NOT EXISTS idx_formations_type ON formations_employes(type_formation);
CREATE INDEX IF NOT EXISTS idx_formations_dates ON formations_employes(date_debut, date_fin);

-- Index sur table carrieres_employes
CREATE INDEX IF NOT EXISTS idx_carrieres_employe ON carrieres_employes(id_employe);
CREATE INDEX IF NOT EXISTS idx_carrieres_type ON carrieres_employes(type_mouvement);
CREATE INDEX IF NOT EXISTS idx_carrieres_date ON carrieres_employes(date_mouvement);

-- Index sur table evaluations_employes
CREATE INDEX IF NOT EXISTS idx_evaluations_employe ON evaluations_employes(id_employe);
CREATE INDEX IF NOT EXISTS idx_evaluations_annee ON evaluations_employes(annee_evaluation);
CREATE INDEX IF NOT EXISTS idx_evaluations_date ON evaluations_employes(date_evaluation);

-- Index sur table departs_employes
CREATE INDEX IF NOT EXISTS idx_departs_employe ON departs_employes(id_employe);
CREATE INDEX IF NOT EXISTS idx_departs_type ON departs_employes(id_type_depart);
CREATE INDEX IF NOT EXISTS idx_departs_date ON departs_employes(date_depart_effectif);

-- Index sur table declarations_sociales
CREATE INDEX IF NOT EXISTS idx_declarations_type ON declarations_sociales(type_declaration);
CREATE INDEX IF NOT EXISTS idx_declarations_periode ON declarations_sociales(periode_reference);
CREATE INDEX IF NOT EXISTS idx_declarations_statut ON declarations_sociales(statut_declaration);

-- Index sur table demandes_employes
CREATE INDEX IF NOT EXISTS idx_demandes_employe ON demandes_employes(id_employe);
CREATE INDEX IF NOT EXISTS idx_demandes_type ON demandes_employes(type_demande);
CREATE INDEX IF NOT EXISTS idx_demandes_statut ON demandes_employes(statut_demande);
CREATE INDEX IF NOT EXISTS idx_demandes_date ON demandes_employes(date_demande);

-- Index sur table alertes_rh
CREATE INDEX IF NOT EXISTS idx_alertes_type ON alertes_rh(type_alerte);
CREATE INDEX IF NOT EXISTS idx_alertes_statut ON alertes_rh(statut_alerte);
CREATE INDEX IF NOT EXISTS idx_alertes_date ON alertes_rh(date_alerte);
CREATE INDEX IF NOT EXISTS idx_alertes_employe ON alertes_rh(id_employe);

-- ============================================
-- COMMENTAIRES SUR LES TABLES PRINCIPALES
-- ============================================

COMMENT ON TABLE employes IS 'Table centrale contenant toutes les informations des employés';
COMMENT ON TABLE bulletins_paie IS 'Bulletins de paie mensuels avec détail des calculs';
COMMENT ON TABLE periodes_paie IS 'Périodes de paie mensuelles avec statuts';
COMMENT ON TABLE conges IS 'Demandes et validations de congés';
COMMENT ON TABLE pointages IS 'Pointages quotidiens des employés';
COMMENT ON TABLE prets IS 'Prêts accordés aux employés avec échéanciers';
COMMENT ON TABLE declarations_sociales IS 'Déclarations CNSS, IRG et INAM';

-- ============================================
-- FIN DU SCRIPT
-- ============================================
