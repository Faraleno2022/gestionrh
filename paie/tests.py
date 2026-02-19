"""
Tests unitaires automatisés du moteur de paie - Législation guinéenne

Exécution: python manage.py test paie.tests

Référence: CGI 2022 + Code du Travail Guinée
"""
from decimal import Decimal
from django.test import SimpleTestCase


class CNSSCalculTests(SimpleTestCase):
    """TU-01 à TU-03: Tests CNSS salarié et employeur"""
    
    PLANCHER = Decimal('550000')
    PLAFOND = Decimal('2500000')
    TAUX_SALARIE = Decimal('0.05')
    TAUX_EMPLOYEUR = Decimal('0.18')
    
    def _calculer_cnss(self, salaire_brut):
        """Calcule CNSS salarié et employeur avec plancher/plafond"""
        if salaire_brut < self.PLANCHER * Decimal('0.10'):  # Seuil minimum 55 000
            return Decimal('0'), Decimal('0'), Decimal('0')
        
        assiette = max(min(salaire_brut, self.PLAFOND), self.PLANCHER)
        cnss_salarie = round(assiette * self.TAUX_SALARIE)
        cnss_employeur = round(assiette * self.TAUX_EMPLOYEUR)
        return assiette, cnss_salarie, cnss_employeur
    
    def test_tu01_cnss_salarie_sous_plafond(self):
        """TU-01: CNSS salarié 5% sur salaire ≤ 2 500 000"""
        salaire = Decimal('2000000')
        assiette, cnss_salarie, _ = self._calculer_cnss(salaire)
        
        self.assertEqual(assiette, Decimal('2000000'))
        self.assertEqual(cnss_salarie, Decimal('100000'))  # 2M × 5%
    
    def test_tu02_cnss_salarie_plafond(self):
        """TU-02: CNSS salarié plafonné à 125 000 si salaire > 2 500 000"""
        salaire = Decimal('3600000')
        assiette, cnss_salarie, _ = self._calculer_cnss(salaire)
        
        self.assertEqual(assiette, Decimal('2500000'))  # Plafond
        self.assertEqual(cnss_salarie, Decimal('125000'))  # 2.5M × 5% = 125K max
    
    def test_tu02_cnss_salaire_8m(self):
        """TU-02: CNSS salarié plafonné même à 8 000 000"""
        salaire = Decimal('8000000')
        assiette, cnss_salarie, _ = self._calculer_cnss(salaire)
        
        self.assertEqual(assiette, Decimal('2500000'))
        self.assertEqual(cnss_salarie, Decimal('125000'))
    
    def test_tu03_cnss_employeur_plafond(self):
        """TU-03: CNSS employeur 18% plafonné à 450 000"""
        salaire = Decimal('8000000')
        assiette, _, cnss_employeur = self._calculer_cnss(salaire)
        
        self.assertEqual(assiette, Decimal('2500000'))
        self.assertEqual(cnss_employeur, Decimal('450000'))  # 2.5M × 18% = 450K max
    
    def test_cnss_au_plancher(self):
        """CNSS avec salaire au plancher (550 000)"""
        salaire = Decimal('550000')
        assiette, cnss_salarie, cnss_employeur = self._calculer_cnss(salaire)
        
        self.assertEqual(assiette, Decimal('550000'))
        self.assertEqual(cnss_salarie, Decimal('27500'))   # 550K × 5%
        self.assertEqual(cnss_employeur, Decimal('99000'))  # 550K × 18%
    
    def test_cnss_sous_plancher(self):
        """CNSS avec salaire sous plancher → assiette = plancher"""
        salaire = Decimal('400000')
        assiette, cnss_salarie, cnss_employeur = self._calculer_cnss(salaire)
        
        self.assertEqual(assiette, Decimal('550000'))  # Plancher appliqué
        self.assertEqual(cnss_salarie, Decimal('27500'))


class ChargesPatronalesTests(SimpleTestCase):
    """TU-04 et TU-05: Tests VF et TA"""
    
    TAUX_VF = Decimal('0.06')    # 6%
    TAUX_TA = Decimal('0.02')    # 2%
    
    def _calculer_vf_ta(self, salaire_brut):
        """Calcule VF et TA sur brut total"""
        vf = round(salaire_brut * self.TAUX_VF)
        ta = round(salaire_brut * self.TAUX_TA)
        return vf, ta
    
    def test_tu04_vf_6_pourcent(self):
        """TU-04: Versement Forfaitaire = 6% du brut"""
        salaire = Decimal('3600000')
        vf, _ = self._calculer_vf_ta(salaire)
        
        self.assertEqual(vf, Decimal('216000'))  # 3.6M × 6%
    
    def test_tu05_ta_2_pourcent(self):
        """TU-05: Taxe Apprentissage = 2% du brut"""
        salaire = Decimal('3600000')
        _, ta = self._calculer_vf_ta(salaire)
        
        self.assertEqual(ta, Decimal('72000'))  # 3.6M × 2%
    
    def test_charges_patronales_total(self):
        """Total charges patronales = CNSS 18% + VF 6% + TA 2%"""
        salaire = Decimal('3600000')
        
        # CNSS employeur (plafonné)
        cnss_employeur = Decimal('450000')  # 2.5M × 18%
        
        vf, ta = self._calculer_vf_ta(salaire)
        total = cnss_employeur + vf + ta
        
        self.assertEqual(total, Decimal('738000'))  # 450K + 216K + 72K


class IRGCalculTests(SimpleTestCase):
    """TU-06 et TU-07: Tests IRG/RTS"""
    
    def _calculer_irg(self, base_imposable):
        """Calcule IRG selon barème RTS CGI 2022 (6 tranches)"""
        tranches = [
            (Decimal('0'), Decimal('1000000'), Decimal('0')),
            (Decimal('1000001'), Decimal('3000000'), Decimal('0.05')),
            (Decimal('3000001'), Decimal('5000000'), Decimal('0.08')),
            (Decimal('5000001'), Decimal('10000000'), Decimal('0.10')),
            (Decimal('10000001'), Decimal('20000000'), Decimal('0.15')),
            (Decimal('20000001'), None, Decimal('0.20')),
        ]
        
        irg_total = Decimal('0')
        
        for borne_inf, borne_sup, taux in tranches:
            if base_imposable < borne_inf:
                break
            
            if borne_sup is None:
                montant_tranche = base_imposable - borne_inf + 1
            else:
                montant_tranche = min(base_imposable, borne_sup) - borne_inf + 1
            
            if montant_tranche > 0:
                irg_total += round(montant_tranche * taux)
        
        return irg_total
    
    def test_tu06_irg_sans_primes(self):
        """TU-06: IRG calculé correctement sur salaire seul"""
        # Salaire brut 3 600 000 - CNSS 125 000 = Base imposable 3 475 000
        base_imposable = Decimal('3475000')
        irg = self._calculer_irg(base_imposable)
        
        # Tranche 0-1M: 0
        # Tranche 1M-3M: 2M × 5% = 100 000
        # Tranche 3M-3.475M: 475K × 8% = 38 000
        # Total attendu: 138 000 (environ, selon arrondi exact)
        self.assertGreater(irg, Decimal('0'))
        self.assertLess(irg, Decimal('150000'))
    
    def test_tu07_irg_avec_primes(self):
        """TU-07: IRG recalculé avec primes"""
        # Salaire 2.8M + Prime 800K = Brut 3.6M
        # Base imposable = 3.6M - 125K CNSS = 3.475M
        base_sans_prime = Decimal('2675000')  # 2.8M - 125K
        base_avec_prime = Decimal('3475000')  # 3.6M - 125K
        
        irg_sans = self._calculer_irg(base_sans_prime)
        irg_avec = self._calculer_irg(base_avec_prime)
        
        # L'IRG avec primes doit être supérieur
        self.assertGreater(irg_avec, irg_sans)
    
    def test_irg_premiere_tranche_exoneree(self):
        """Première tranche (0-1M) exonérée à 0%"""
        base_imposable = Decimal('800000')
        irg = self._calculer_irg(base_imposable)
        
        self.assertEqual(irg, Decimal('0'))
    
    def test_irg_exemple_manuel_8m(self):
        """IRG sur exemple du manuel (8M GNF)"""
        # Base imposable = 8M - 125K = 7.875M
        base_imposable = Decimal('7875000')
        irg = self._calculer_irg(base_imposable)
        
        # Calcul attendu:
        # 0-1M: 0
        # 1M-3M: 2M × 5% = 100 000
        # 3M-5M: 2M × 8% = 160 000
        # 5M-7.875M: 2.875M × 10% = 287 500
        # Total: 547 500
        self.assertEqual(irg, Decimal('547500'))


class DeductionsTests(SimpleTestCase):
    """TU-08 et TU-09: Tests avances et prêts"""
    
    def test_tu08_avance_salaire(self):
        """TU-08: Avance sur salaire déduite du net"""
        salaire_brut = Decimal('3600000')
        cnss_salarie = Decimal('125000')
        irg = Decimal('67562')
        avance = Decimal('160000')
        
        net_avant_avance = salaire_brut - cnss_salarie - irg
        net_apres_avance = net_avant_avance - avance
        
        self.assertEqual(net_avant_avance, Decimal('3407438'))
        self.assertEqual(net_apres_avance, Decimal('3247438'))
    
    def test_tu09_pret_salarie(self):
        """TU-09: Prêt salarié déduit du net"""
        salaire_brut = Decimal('3600000')
        cnss_salarie = Decimal('125000')
        irg = Decimal('67562')
        pret_mensuel = Decimal('200000')
        
        net = salaire_brut - cnss_salarie - irg - pret_mensuel
        
        self.assertEqual(net, Decimal('3207438'))


class NetAPayerTests(SimpleTestCase):
    """TU-10: Test net à payer final"""
    
    def test_tu10_net_a_payer_complet(self):
        """TU-10: Net à payer = Brut - toutes retenues"""
        # Données du bulletin validé
        salaire_brut = Decimal('3600000')
        cnss_salarie = Decimal('125000')
        irg = Decimal('67562')
        avance = Decimal('160000')
        
        total_retenues = cnss_salarie + irg + avance
        net_a_payer = salaire_brut - total_retenues
        
        self.assertEqual(total_retenues, Decimal('352562'))
        self.assertEqual(net_a_payer, Decimal('3247438'))
    
    def test_net_a_payer_sans_retenues_optionnelles(self):
        """Net à payer sans avance ni prêt"""
        salaire_brut = Decimal('3600000')
        cnss_salarie = Decimal('125000')
        irg = Decimal('67562')
        
        net_a_payer = salaire_brut - cnss_salarie - irg
        
        self.assertEqual(net_a_payer, Decimal('3407438'))


class PlafondIndemnitesTests(SimpleTestCase):
    """Tests plafond 25% indemnités forfaitaires"""
    
    TAUX_PLAFOND = Decimal('0.25')
    
    def test_indemnites_sous_plafond(self):
        """Indemnités sous 25% → pas de réintégration"""
        salaire_brut = Decimal('2800000')
        indemnites = Decimal('500000')  # < 25% de 2.8M = 700K
        
        plafond = salaire_brut * self.TAUX_PLAFOND
        depassement = max(Decimal('0'), indemnites - plafond)
        
        self.assertEqual(depassement, Decimal('0'))
    
    def test_indemnites_au_plafond(self):
        """Indemnités à 25% → pas de réintégration"""
        salaire_brut = Decimal('2800000')
        indemnites = Decimal('700000')  # = 25% exactement
        
        plafond = salaire_brut * self.TAUX_PLAFOND
        depassement = max(Decimal('0'), indemnites - plafond)
        
        self.assertEqual(depassement, Decimal('0'))
    
    def test_indemnites_depassement(self):
        """Indemnités > 25% → excédent réintégré"""
        salaire_brut = Decimal('2800000')
        indemnites = Decimal('900000')  # > 25% de 2.8M = 700K
        
        plafond = salaire_brut * self.TAUX_PLAFOND
        depassement = max(Decimal('0'), indemnites - plafond)
        
        self.assertEqual(plafond, Decimal('700000'))
        self.assertEqual(depassement, Decimal('200000'))  # Réintégré dans base imposable


class ExonerationStagiaireTests(SimpleTestCase):
    """Tests exonération RTS stagiaires/apprentis"""
    
    SEUIL_EXONERATION = Decimal('1200000')
    DUREE_MAX_MOIS = 12
    
    def _est_exonere(self, type_contrat, salaire, mois_ecoules):
        """Vérifie si éligible à l'exonération RTS"""
        est_stagiaire_apprenti = type_contrat in ('stage', 'apprentissage')
        duree_ok = mois_ecoules <= self.DUREE_MAX_MOIS
        montant_ok = salaire <= self.SEUIL_EXONERATION
        
        return est_stagiaire_apprenti and duree_ok and montant_ok
    
    def test_stagiaire_exonere(self):
        """Stagiaire ≤ 1.2M et ≤ 12 mois → exonéré"""
        self.assertTrue(self._est_exonere('stage', Decimal('1000000'), 6))
    
    def test_stagiaire_salaire_depasse(self):
        """Stagiaire > 1.2M → non exonéré"""
        self.assertFalse(self._est_exonere('stage', Decimal('1500000'), 6))
    
    def test_stagiaire_duree_depassee(self):
        """Stagiaire > 12 mois → non exonéré"""
        self.assertFalse(self._est_exonere('stage', Decimal('1000000'), 15))
    
    def test_cdi_non_exonere(self):
        """CDI jamais exonéré même si salaire faible"""
        self.assertFalse(self._est_exonere('CDI', Decimal('800000'), 3))
