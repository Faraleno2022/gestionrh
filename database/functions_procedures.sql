-- ============================================
-- FONCTIONS ET PROCÉDURES STOCKÉES
-- GESTIONNAIRE RH GUINÉE
-- ============================================

-- ============================================
-- 1. FONCTIONS DE CALCUL DE PAIE
-- ============================================

-- Fonction: Calculer la base CNSS (plafonnée)
CREATE OR REPLACE FUNCTION calcul_base_cnss(salaire_brut DECIMAL)
RETURNS DECIMAL AS $$
DECLARE
    plafond_cnss DECIMAL;
BEGIN
    SELECT valeur_numerique INTO plafond_cnss 
    FROM parametres_paie 
    WHERE code_parametre = 'PLAFOND_CNSS' AND actif = TRUE;
    
    RETURN LEAST(salaire_brut, plafond_cnss);
END;
$$ LANGUAGE plpgsql;

-- Fonction: Calculer la cotisation CNSS employé
CREATE OR REPLACE FUNCTION calcul_cnss_employe(salaire_brut DECIMAL)
RETURNS DECIMAL AS $$
DECLARE
    base_cnss DECIMAL;
    taux_cnss DECIMAL;
BEGIN
    base_cnss := calcul_base_cnss(salaire_brut);
    
    SELECT valeur_numerique INTO taux_cnss 
    FROM parametres_paie 
    WHERE code_parametre = 'TAUX_CNSS_EMPLOYE' AND actif = TRUE;
    
    RETURN ROUND(base_cnss * taux_cnss / 100, 0);
END;
$$ LANGUAGE plpgsql;

-- Fonction: Calculer la cotisation CNSS employeur
CREATE OR REPLACE FUNCTION calcul_cnss_employeur(salaire_brut DECIMAL)
RETURNS DECIMAL AS $$
DECLARE
    base_cnss DECIMAL;
    taux_cnss DECIMAL;
BEGIN
    base_cnss := calcul_base_cnss(salaire_brut);
    
    SELECT valeur_numerique INTO taux_cnss 
    FROM parametres_paie 
    WHERE code_parametre = 'TAUX_CNSS_EMPLOYEUR' AND actif = TRUE;
    
    RETURN ROUND(base_cnss * taux_cnss / 100, 0);
END;
$$ LANGUAGE plpgsql;

-- Fonction: Calculer la cotisation INAM
CREATE OR REPLACE FUNCTION calcul_inam(salaire_brut DECIMAL)
RETURNS DECIMAL AS $$
DECLARE
    plafond_inam DECIMAL;
    taux_inam DECIMAL;
    base_inam DECIMAL;
BEGIN
    SELECT valeur_numerique INTO plafond_inam 
    FROM parametres_paie 
    WHERE code_parametre = 'PLAFOND_INAM' AND actif = TRUE;
    
    SELECT valeur_numerique INTO taux_inam 
    FROM parametres_paie 
    WHERE code_parametre = 'TAUX_INAM' AND actif = TRUE;
    
    base_inam := LEAST(salaire_brut, plafond_inam);
    
    RETURN ROUND(base_inam * taux_inam / 100, 0);
END;
$$ LANGUAGE plpgsql;

-- Fonction: Calculer l'abattement IRG
CREATE OR REPLACE FUNCTION calcul_abattement_irg(salaire_brut DECIMAL)
RETURNS DECIMAL AS $$
DECLARE
    taux_abattement DECIMAL;
    plafond_abattement DECIMAL;
    abattement DECIMAL;
BEGIN
    SELECT valeur_numerique INTO taux_abattement 
    FROM parametres_paie 
    WHERE code_parametre = 'ABATTEMENT_IRG' AND actif = TRUE;
    
    SELECT valeur_numerique INTO plafond_abattement 
    FROM parametres_paie 
    WHERE code_parametre = 'PLAFOND_ABATTEMENT_IRG' AND actif = TRUE;
    
    abattement := salaire_brut * taux_abattement / 100;
    
    RETURN LEAST(abattement, plafond_abattement);
END;
$$ LANGUAGE plpgsql;

-- Fonction: Calculer l'IRG selon le barème progressif
CREATE OR REPLACE FUNCTION calcul_irg(salaire_brut DECIMAL, cnss_employe DECIMAL, inam_employe DECIMAL)
RETURNS DECIMAL AS $$
DECLARE
    base_irg DECIMAL;
    abattement DECIMAL;
    net_imposable DECIMAL;
    irg_total DECIMAL := 0;
    tranche RECORD;
    montant_tranche DECIMAL;
    annee_courante INT;
BEGIN
    -- Calcul de la base IRG
    base_irg := salaire_brut - cnss_employe - inam_employe;
    
    -- Calcul de l'abattement
    abattement := calcul_abattement_irg(base_irg);
    
    -- Net imposable
    net_imposable := base_irg - abattement;
    
    IF net_imposable <= 0 THEN
        RETURN 0;
    END IF;
    
    -- Année courante
    annee_courante := DATE_PART('year', CURRENT_DATE);
    
    -- Calcul progressif par tranche
    FOR tranche IN 
        SELECT * FROM tranches_irg 
        WHERE annee_validite = annee_courante AND actif = TRUE
        ORDER BY numero_tranche
    LOOP
        IF net_imposable > tranche.borne_inferieure THEN
            IF tranche.borne_superieure IS NULL THEN
                -- Dernière tranche (sans limite supérieure)
                montant_tranche := net_imposable - tranche.borne_inferieure;
            ELSE
                montant_tranche := LEAST(net_imposable, tranche.borne_superieure) - tranche.borne_inferieure;
            END IF;
            
            irg_total := irg_total + (montant_tranche * tranche.taux_irg / 100);
        END IF;
    END LOOP;
    
    RETURN ROUND(irg_total, 0);
END;
$$ LANGUAGE plpgsql;

-- Fonction: Calculer le salaire net à payer
CREATE OR REPLACE FUNCTION calcul_net_a_payer(
    salaire_brut DECIMAL,
    cnss_employe DECIMAL,
    inam_employe DECIMAL,
    irg DECIMAL,
    autres_retenues DECIMAL DEFAULT 0
)
RETURNS DECIMAL AS $$
BEGIN
    RETURN salaire_brut - cnss_employe - inam_employe - irg - autres_retenues;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 2. FONCTIONS DE GESTION DES CONGÉS
-- ============================================

-- Fonction: Calculer le nombre de jours ouvrables entre deux dates
CREATE OR REPLACE FUNCTION calcul_jours_ouvrables(date_debut DATE, date_fin DATE)
RETURNS INT AS $$
DECLARE
    nb_jours INT := 0;
    date_courante DATE;
    jour_semaine INT;
BEGIN
    date_courante := date_debut;
    
    WHILE date_courante <= date_fin LOOP
        jour_semaine := EXTRACT(DOW FROM date_courante);
        
        -- Exclure samedi (6) et dimanche (0)
        IF jour_semaine NOT IN (0, 6) THEN
            -- Vérifier si ce n'est pas un jour férié
            IF NOT EXISTS (
                SELECT 1 FROM calendrier_jours_feries 
                WHERE date_jour_ferie = date_courante
            ) THEN
                nb_jours := nb_jours + 1;
            END IF;
        END IF;
        
        date_courante := date_courante + INTERVAL '1 day';
    END LOOP;
    
    RETURN nb_jours;
END;
$$ LANGUAGE plpgsql;

-- Fonction: Vérifier la disponibilité du solde de congés
CREATE OR REPLACE FUNCTION verifier_solde_conges(
    p_id_employe INT,
    p_annee INT,
    p_nb_jours DECIMAL
)
RETURNS BOOLEAN AS $$
DECLARE
    solde_disponible DECIMAL;
BEGIN
    SELECT conges_restants INTO solde_disponible
    FROM soldes_conges
    WHERE id_employe = p_id_employe AND annee = p_annee;
    
    IF solde_disponible IS NULL THEN
        RETURN FALSE;
    END IF;
    
    RETURN solde_disponible >= p_nb_jours;
END;
$$ LANGUAGE plpgsql;

-- Fonction: Mettre à jour le solde de congés
CREATE OR REPLACE FUNCTION maj_solde_conges(
    p_id_employe INT,
    p_annee INT,
    p_nb_jours DECIMAL
)
RETURNS VOID AS $$
BEGIN
    UPDATE soldes_conges
    SET conges_pris = conges_pris + p_nb_jours,
        conges_restants = conges_restants - p_nb_jours,
        date_mise_a_jour = CURRENT_DATE
    WHERE id_employe = p_id_employe AND annee = p_annee;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 3. FONCTIONS DE CALCUL D'ANCIENNETÉ
-- ============================================

-- Fonction: Calculer l'ancienneté en années
CREATE OR REPLACE FUNCTION calcul_anciennete_annees(date_embauche DATE)
RETURNS INT AS $$
BEGIN
    RETURN DATE_PART('year', AGE(CURRENT_DATE, date_embauche));
END;
$$ LANGUAGE plpgsql;

-- Fonction: Calculer la prime d'ancienneté (exemple: 2% par an, max 20%)
CREATE OR REPLACE FUNCTION calcul_prime_anciennete(salaire_base DECIMAL, date_embauche DATE)
RETURNS DECIMAL AS $$
DECLARE
    anciennete_annees INT;
    taux_prime DECIMAL;
BEGIN
    anciennete_annees := calcul_anciennete_annees(date_embauche);
    
    -- 2% par année d'ancienneté, plafonné à 20% (10 ans)
    taux_prime := LEAST(anciennete_annees * 2, 20);
    
    RETURN ROUND(salaire_base * taux_prime / 100, 0);
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 4. FONCTIONS DE CALCUL D'INDEMNITÉS DE DÉPART
-- ============================================

-- Fonction: Calculer l'indemnité de licenciement
CREATE OR REPLACE FUNCTION calcul_indemnite_licenciement(
    p_id_employe INT,
    salaire_mensuel DECIMAL
)
RETURNS DECIMAL AS $$
DECLARE
    anciennete_annees INT;
    indemnite DECIMAL;
    date_embauche DATE;
BEGIN
    SELECT e.date_embauche INTO date_embauche
    FROM employes e
    WHERE id_employe = p_id_employe;
    
    anciennete_annees := calcul_anciennete_annees(date_embauche);
    
    -- Selon le Code du Travail guinéen:
    -- 1 mois de salaire par année d'ancienneté (simplifié)
    indemnite := salaire_mensuel * anciennete_annees;
    
    RETURN ROUND(indemnite, 0);
END;
$$ LANGUAGE plpgsql;

-- Fonction: Calculer l'indemnité de congés non pris
CREATE OR REPLACE FUNCTION calcul_indemnite_conges(
    p_id_employe INT,
    salaire_journalier DECIMAL
)
RETURNS DECIMAL AS $$
DECLARE
    conges_restants DECIMAL;
    annee_courante INT;
BEGIN
    annee_courante := DATE_PART('year', CURRENT_DATE);
    
    SELECT sc.conges_restants INTO conges_restants
    FROM soldes_conges sc
    WHERE id_employe = p_id_employe AND annee = annee_courante;
    
    IF conges_restants IS NULL THEN
        conges_restants := 0;
    END IF;
    
    RETURN ROUND(conges_restants * salaire_journalier, 0);
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 5. PROCÉDURES DE GESTION
-- ============================================

-- Procédure: Initialiser le solde de congés annuel pour tous les employés
CREATE OR REPLACE PROCEDURE init_soldes_conges_annee(p_annee INT)
LANGUAGE plpgsql AS $$
DECLARE
    jours_conges DECIMAL;
BEGIN
    -- Récupérer le nombre de jours de congés légaux
    SELECT valeur_numerique INTO jours_conges
    FROM parametres_paie
    WHERE code_parametre = 'JOURS_CONGES_ANNUELS' AND actif = TRUE;
    
    -- Insérer les soldes pour tous les employés actifs
    INSERT INTO soldes_conges (id_employe, annee, conges_acquis, conges_restants)
    SELECT 
        id_employe,
        p_annee,
        jours_conges,
        jours_conges
    FROM employes
    WHERE statut_employe = 'Actif'
    ON CONFLICT (id_employe, annee) DO NOTHING;
    
    RAISE NOTICE 'Soldes de congés initialisés pour l''année %', p_annee;
END;
$$;

-- Procédure: Générer les alertes pour les contrats arrivant à échéance
CREATE OR REPLACE PROCEDURE generer_alertes_contrats()
LANGUAGE plpgsql AS $$
DECLARE
    contrat RECORD;
    jours_avant_echeance INT;
BEGIN
    FOR contrat IN 
        SELECT ce.*, e.nom, e.prenoms
        FROM contrats_employes ce
        INNER JOIN employes e ON ce.id_employe = e.id_employe
        WHERE ce.statut_contrat = 'En cours'
          AND ce.date_fin IS NOT NULL
          AND ce.date_fin BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '90 days'
          AND e.statut_employe = 'Actif'
    LOOP
        jours_avant_echeance := contrat.date_fin - CURRENT_DATE;
        
        -- Créer une alerte si elle n'existe pas déjà
        INSERT INTO alertes_rh (
            type_alerte,
            priorite,
            id_employe,
            titre_alerte,
            description_alerte,
            date_alerte,
            date_echeance,
            statut_alerte
        )
        SELECT
            'Fin_contrat',
            CASE 
                WHEN jours_avant_echeance <= 30 THEN 'Haute'
                WHEN jours_avant_echeance <= 60 THEN 'Moyenne'
                ELSE 'Basse'
            END,
            contrat.id_employe,
            'Contrat arrivant à échéance',
            'Le contrat de ' || contrat.nom || ' ' || contrat.prenoms || 
            ' arrive à échéance le ' || TO_CHAR(contrat.date_fin, 'DD/MM/YYYY') ||
            ' (dans ' || jours_avant_echeance || ' jours)',
            CURRENT_DATE,
            contrat.date_fin,
            'Active'
        WHERE NOT EXISTS (
            SELECT 1 FROM alertes_rh
            WHERE type_alerte = 'Fin_contrat'
              AND id_employe = contrat.id_employe
              AND date_echeance = contrat.date_fin
              AND statut_alerte = 'Active'
        );
    END LOOP;
    
    RAISE NOTICE 'Alertes de fin de contrat générées';
END;
$$;

-- Procédure: Calculer les cumuls de paie mensuels
CREATE OR REPLACE PROCEDURE calculer_cumuls_paie(p_annee INT, p_mois INT)
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO cumuls_paie (
        id_employe, annee, mois, type_cumul,
        cumul_salaire_base, cumul_brut, cumul_cnss_employe,
        cumul_cnss_employeur, cumul_inam, cumul_irg,
        cumul_retenues, cumul_net_paye
    )
    SELECT 
        bp.id_employe,
        p_annee,
        p_mois,
        'Mensuel',
        SUM(COALESCE(lb.montant, 0)) FILTER (WHERE r.code_rubrique = 'SAL_BASE'),
        SUM(bp.salaire_brut),
        SUM(bp.cnss_employe),
        SUM(bp.cnss_employeur),
        SUM(bp.inam_employe),
        SUM(bp.irg),
        SUM(bp.total_retenues),
        SUM(bp.net_a_payer)
    FROM bulletins_paie bp
    LEFT JOIN lignes_bulletin lb ON bp.id_bulletin = lb.id_bulletin
    LEFT JOIN rubriques_paie r ON lb.id_rubrique = r.id_rubrique
    WHERE bp.annee_paie = p_annee AND bp.mois_paie = p_mois
    GROUP BY bp.id_employe
    ON CONFLICT (id_employe, annee, mois, type_cumul) 
    DO UPDATE SET
        cumul_salaire_base = EXCLUDED.cumul_salaire_base,
        cumul_brut = EXCLUDED.cumul_brut,
        cumul_cnss_employe = EXCLUDED.cumul_cnss_employe,
        cumul_cnss_employeur = EXCLUDED.cumul_cnss_employeur,
        cumul_inam = EXCLUDED.cumul_inam,
        cumul_irg = EXCLUDED.cumul_irg,
        cumul_retenues = EXCLUDED.cumul_retenues,
        cumul_net_paye = EXCLUDED.cumul_net_paye,
        date_mise_a_jour = CURRENT_TIMESTAMP;
    
    RAISE NOTICE 'Cumuls mensuels calculés pour %/%', p_mois, p_annee;
END;
$$;

-- ============================================
-- 6. TRIGGERS
-- ============================================

-- Trigger: Mettre à jour la date de modification d'un employé
CREATE OR REPLACE FUNCTION trigger_maj_date_modification_employe()
RETURNS TRIGGER AS $$
BEGIN
    NEW.date_modification = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_employe_modification
    BEFORE UPDATE ON employes
    FOR EACH ROW
    EXECUTE FUNCTION trigger_maj_date_modification_employe();

-- Trigger: Logger les modifications importantes
CREATE OR REPLACE FUNCTION trigger_log_modification()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO historique_modifications (
        table_modifiee,
        id_enregistrement,
        type_operation,
        anciennes_valeurs,
        nouvelles_valeurs,
        date_modification
    ) VALUES (
        TG_TABLE_NAME,
        COALESCE(NEW.id_employe, OLD.id_employe),
        TG_OP,
        row_to_json(OLD),
        row_to_json(NEW),
        CURRENT_TIMESTAMP
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Appliquer le trigger sur les tables sensibles
CREATE TRIGGER trg_log_employes
    AFTER INSERT OR UPDATE OR DELETE ON employes
    FOR EACH ROW
    EXECUTE FUNCTION trigger_log_modification();

-- Trigger: Valider les dates de congés
CREATE OR REPLACE FUNCTION trigger_valider_dates_conges()
RETURNS TRIGGER AS $$
BEGIN
    -- Vérifier que la date de fin est après la date de début
    IF NEW.date_fin <= NEW.date_debut THEN
        RAISE EXCEPTION 'La date de fin doit être postérieure à la date de début';
    END IF;
    
    -- Calculer le nombre de jours ouvrables
    NEW.nombre_jours := calcul_jours_ouvrables(NEW.date_debut, NEW.date_fin);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_valider_conges
    BEFORE INSERT OR UPDATE ON conges
    FOR EACH ROW
    EXECUTE FUNCTION trigger_valider_dates_conges();

-- Trigger: Mettre à jour le solde de congés après approbation
CREATE OR REPLACE FUNCTION trigger_maj_solde_apres_approbation()
RETURNS TRIGGER AS $$
BEGIN
    -- Si le congé vient d'être approuvé
    IF NEW.statut_demande = 'Approuvé' AND OLD.statut_demande != 'Approuvé' THEN
        PERFORM maj_solde_conges(NEW.id_employe, NEW.annee_reference, NEW.nombre_jours);
    END IF;
    
    -- Si le congé est annulé, recréditer le solde
    IF NEW.statut_demande = 'Annulé' AND OLD.statut_demande = 'Approuvé' THEN
        PERFORM maj_solde_conges(NEW.id_employe, NEW.annee_reference, -NEW.nombre_jours);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_maj_solde_conges
    AFTER UPDATE ON conges
    FOR EACH ROW
    EXECUTE FUNCTION trigger_maj_solde_apres_approbation();

-- ============================================
-- 7. FONCTIONS UTILITAIRES
-- ============================================

-- Fonction: Générer un numéro de matricule automatique
CREATE OR REPLACE FUNCTION generer_matricule()
RETURNS VARCHAR AS $$
DECLARE
    annee VARCHAR(4);
    numero_seq INT;
    nouveau_matricule VARCHAR(20);
BEGIN
    annee := TO_CHAR(CURRENT_DATE, 'YYYY');
    
    SELECT COALESCE(MAX(CAST(SUBSTRING(matricule FROM 5) AS INT)), 0) + 1
    INTO numero_seq
    FROM employes
    WHERE matricule LIKE annee || '%';
    
    nouveau_matricule := annee || LPAD(numero_seq::TEXT, 4, '0');
    
    RETURN nouveau_matricule;
END;
$$ LANGUAGE plpgsql;

-- Fonction: Vérifier si un employé est en congé à une date donnée
CREATE OR REPLACE FUNCTION est_en_conge(p_id_employe INT, p_date DATE)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM conges
        WHERE id_employe = p_id_employe
          AND statut_demande = 'Approuvé'
          AND p_date BETWEEN date_debut AND date_fin
    );
END;
$$ LANGUAGE plpgsql;

-- Fonction: Calculer le taux d'absentéisme d'un employé
CREATE OR REPLACE FUNCTION calcul_taux_absenteisme(
    p_id_employe INT,
    p_date_debut DATE,
    p_date_fin DATE
)
RETURNS DECIMAL AS $$
DECLARE
    nb_jours_travailles INT;
    nb_jours_absents INT;
    taux DECIMAL;
BEGIN
    nb_jours_travailles := calcul_jours_ouvrables(p_date_debut, p_date_fin);
    
    SELECT COUNT(*) INTO nb_jours_absents
    FROM pointages
    WHERE id_employe = p_id_employe
      AND date_pointage BETWEEN p_date_debut AND p_date_fin
      AND statut_pointage IN ('Absent', 'Absence justifiée');
    
    IF nb_jours_travailles = 0 THEN
        RETURN 0;
    END IF;
    
    taux := (nb_jours_absents::DECIMAL / nb_jours_travailles) * 100;
    
    RETURN ROUND(taux, 2);
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- FIN DU SCRIPT
-- ============================================

-- Afficher les fonctions créées
SELECT 'Fonctions et procédures créées avec succès!' AS statut;
