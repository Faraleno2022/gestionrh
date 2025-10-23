-- ============================================
-- STRUCTURE BASE DE DONNÉES RH GUINÉE
-- Système de Gestion des Ressources Humaines
-- Conforme au Code du Travail Guinéen
-- ============================================

-- Ce fichier contient la structure complète de la base de données
-- pour un système RH complet incluant :
-- - Gestion des employés
-- - Paie et cotisations sociales (CNSS, INAM, IRG)
-- - Temps de travail et congés
-- - Recrutement
-- - Formation et carrière
-- - Déclarations sociales
-- - Portail employé

-- IMPORTANT : Cette structure est conçue pour PostgreSQL
-- Pour SQLite (développement), Django ORM gère automatiquement
-- les différences de syntaxe

-- ============================================
-- MODULES IMPLÉMENTÉS
-- ============================================
-- ✅ 1. Système et Sécurité (utilisateurs, profils, droits)
-- ✅ 2. Configuration Entreprise (société, établissements)
-- ✅ 3. Organisation (services, postes)
-- ✅ 4. Employés (données complètes)
-- ⏳ 5. Formation et Carrière
-- ⏳ 6. Temps de Travail (pointages, congés, absences)
-- ⏳ 7. Paie - Paramétrage
-- ⏳ 8. Paie - Éléments salariaux
-- ⏳ 9. Paie - Bulletins
-- ⏳ 10. Acomptes et Prêts
-- ⏳ 11. Recrutement
-- ⏳ 12. Départs
-- ⏳ 13. Dashboard & Statistiques
-- ⏳ 14. Sanctions Disciplinaires
-- ⏳ 15. Portail Employé
-- ⏳ 16. Comptabilité & Déclarations
-- ⏳ 17. Audit & Sauvegarde
-- ⏳ 18. Signature Électronique

-- ============================================
-- LÉGENDE
-- ============================================
-- ✅ Implémenté dans Django
-- ⏳ À implémenter
-- 🇬🇳 Spécifique à la Guinée

-- ============================================
-- NOTES IMPORTANTES
-- ============================================
-- 1. CNSS : Caisse Nationale de Sécurité Sociale
--    - Part employé : 5%
--    - Part employeur : 18%
--    - Plafond : À définir selon législation

-- 2. INAM : Institut National d'Assurance Maladie
--    - Taux : 2.5%

-- 3. IRG : Impôt sur les Revenus de Guinée
--    - Barème progressif par tranches
--    - Abattement forfaitaire

-- 4. Congés annuels : 26 jours ouvrables
--    (selon Code du Travail Guinéen)

-- 5. SMIG : Salaire Minimum Interprofessionnel Garanti
--    (à paramétrer selon décrets)

-- ============================================
-- PROCHAINES ÉTAPES D'IMPLÉMENTATION
-- ============================================
-- Phase 1 : Modules de base (✅ Complété)
-- Phase 2 : Temps de travail et congés
-- Phase 3 : Paie complète avec calculs
-- Phase 4 : Déclarations sociales
-- Phase 5 : Portail employé et workflow
-- Phase 6 : Reporting avancé et BI

-- Pour voir la structure SQL complète, consultez :
-- docs/STRUCTURE_SQL_POSTGRESQL.sql
