"""
Services de calcul de paie
Moteur de calcul automatique conforme à la législation guinéenne
"""
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta
from django.db import transaction
from django.db import models
from django.utils import timezone

from .models import (
    BulletinPaie, LigneBulletin, ElementSalaire, CumulPaie,
    RubriquePaie, Constante, TrancheIRG, PeriodePaie, HistoriquePaie
)
from employes.models import Employe
from temps_travail.models import Pointage, Absence, Conge
from core.services.devises import DeviseService
from core.models import Devise
import calendar


class MoteurCalculPaie:
    """Moteur de calcul automatique de la paie"""
    
    def __init__(self, employe, periode):
        self.employe = employe
        self.periode = periode
        self.lignes = []
        self.montants = {
            'brut': Decimal('0'),
            'imposable': Decimal('0'),
            'cnss_base': Decimal('0'),
            'cnss_employe': Decimal('0'),
            'cnss_employeur': Decimal('0'),
            'irg': Decimal('0'),
            'net': Decimal('0'),
            'total_gains': Decimal('0'),
            'total_retenues': Decimal('0'),
            # Charges patronales supplémentaires
            'versement_forfaitaire': Decimal('0'),  # VF 6%
            'taxe_apprentissage': Decimal('0'),     # TA 2% (CGI 2022)
            'total_charges_patronales': Decimal('0'),
            # Exonération RTS stagiaires/apprentis
            'exoneration_rts': False,
            'raison_exoneration_rts': '',
            # Plafond 25% indemnités forfaitaires
            'indemnites_forfaitaires': Decimal('0'),
            'plafond_indemnites': Decimal('0'),
            'depassement_plafond_indemnites': Decimal('0'),
            'reintegration_base_imposable': Decimal('0'),
            # Temps de travail
            'jours_travailles': Decimal('0'),
            'jours_ouvrables': Decimal('0'),
            'heures_travaillees': Decimal('0'),
            'heures_supplementaires': Decimal('0'),
            'jours_absence': Decimal('0'),
            'jours_conge': Decimal('0'),
            'retenue_absence': Decimal('0'),
        }
        self.constantes = self._charger_constantes()
        self.tranches_irg = self._charger_tranches_irg()
        
        # Devise de paie de l'employé et service de conversion
        self.devise_employe = employe.devise_paie if employe.devise_paie else DeviseService.get_devise_base()
        self.devise_base = DeviseService.get_devise_base()
        self.date_conversion = date(self.periode.annee, self.periode.mois, 1)
    
    def _charger_constantes(self):
        """Charger les constantes actives"""
        constantes = {}
        for const in Constante.objects.filter(actif=True):
            constantes[const.code] = const.valeur
        return constantes
    
    def _charger_tranches_irg(self):
        """Charger le barème IRG"""
        return TrancheIRG.objects.filter(
            annee_validite=self.periode.annee,
            actif=True
        ).order_by('numero_tranche')
    
    def _arrondir(self, montant):
        """Arrondir un montant à 2 décimales"""
        return montant.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _calculer_anciennete(self):
        """Calculer l'ancienneté en années"""
        if not self.employe.date_embauche:
            return 0
        
        delta = date(self.periode.annee, self.periode.mois, 1) - self.employe.date_embauche
        return delta.days // 365
    
    def _obtenir_taux_anciennete(self, annees):
        """Obtenir le taux d'ancienneté selon le barème"""
        if annees < 2:
            return self.constantes.get('ANCIEN_0_2ANS', Decimal('2.00'))
        elif annees < 5:
            return self.constantes.get('ANCIEN_2_5ANS', Decimal('5.00'))
        elif annees < 10:
            return self.constantes.get('ANCIEN_5_10ANS', Decimal('7.00'))
        elif annees < 15:
            return self.constantes.get('ANCIEN_10_15ANS', Decimal('10.00'))
        else:
            return self.constantes.get('ANCIEN_15ANS_PLUS', Decimal('12.00'))
    
    def calculer_bulletin(self):
        """Calculer le bulletin de paie complet"""
        
        # Initialiser les alertes
        self.montants['alertes'] = []
        
        # 0. Calculer le temps de travail (pointages, absences, congés)
        self._calculer_temps_travail()
        
        # 1. Calculer les gains
        self._calculer_gains()
        
        # 2. Appliquer les retenues pour absences non payées
        self._appliquer_retenues_absences()
        
        # 3. Calculer le brut
        self.montants['brut'] = self.montants['total_gains'] - self.montants['retenue_absence']
        
        # 3.1 Vérification: Salaire brut très faible ou nul
        plancher_cnss = self.constantes.get('PLANCHER_CNSS', Decimal('550000'))
        seuil_minimum = plancher_cnss * Decimal('0.10')  # 10% du plancher = 55 000 GNF
        
        if self.montants['brut'] <= 0:
            self.montants['alertes'].append({
                'type': 'critique',
                'message': f"Salaire brut nul ou négatif ({self.montants['brut']:,.0f} GNF). Vérifiez les éléments de salaire."
            })
        elif self.montants['brut'] < seuil_minimum:
            self.montants['alertes'].append({
                'type': 'avertissement',
                'message': f"Salaire brut très faible ({self.montants['brut']:,.0f} GNF < {seuil_minimum:,.0f} GNF). Pas de cotisation CNSS calculée."
            })
        
        # 4. Calculer les cotisations sociales
        self._calculer_cotisations_sociales()
        
        # 5. Calculer l'IRG/IRSA
        self._calculer_irg()
        
        # 6. Calculer les autres retenues
        self._calculer_autres_retenues()
        
        # 7. Calculer le net
        net_calcule = self.montants['brut'] - self.montants['total_retenues']
        
        # 7.1 Protection: Empêcher le net négatif
        # Si les retenues dépassent le brut, on plafonne les retenues au brut
        if net_calcule < 0:
            self.montants['alertes'].append({
                'type': 'critique',
                'message': f"Net à payer serait négatif ({net_calcule:,.0f} GNF). Les retenues ({self.montants['total_retenues']:,.0f} GNF) dépassent le brut ({self.montants['brut']:,.0f} GNF). Retenues plafonnées."
            })
            # Plafonner les retenues au montant du brut pour éviter un net négatif
            self.montants['retenues_excessives'] = abs(net_calcule)
            self.montants['total_retenues'] = self.montants['brut']
            self.montants['net'] = Decimal('0')
        else:
            self.montants['retenues_excessives'] = Decimal('0')
            self.montants['net'] = net_calcule
        
        return self.montants
    
    def _calculer_temps_travail(self):
        """Calculer les données de temps de travail pour la période"""
        # Dates de la période
        premier_jour = date(self.periode.annee, self.periode.mois, 1)
        dernier_jour = date(
            self.periode.annee, 
            self.periode.mois, 
            calendar.monthrange(self.periode.annee, self.periode.mois)[1]
        )
        
        # Calculer les jours ouvrables du mois (lundi-vendredi)
        jours_ouvrables = 0
        current = premier_jour
        while current <= dernier_jour:
            if current.weekday() < 5:  # Lundi=0, Vendredi=4
                jours_ouvrables += 1
            current += timedelta(days=1)
        
        self.montants['jours_ouvrables'] = Decimal(str(jours_ouvrables))
        
        # Récupérer les pointages du mois
        pointages = Pointage.objects.filter(
            employe=self.employe,
            date_pointage__gte=premier_jour,
            date_pointage__lte=dernier_jour
        )
        
        # Compter les jours travaillés
        jours_presents = pointages.filter(statut_pointage='present').count()
        jours_retard = pointages.filter(statut_pointage='retard').count()
        self.montants['jours_travailles'] = Decimal(str(jours_presents + jours_retard))
        
        # Heures travaillées et supplémentaires
        from django.db.models import Sum
        heures = pointages.aggregate(
            heures_travaillees=Sum('heures_travaillees'),
            heures_sup=Sum('heures_supplementaires')
        )
        self.montants['heures_travaillees'] = heures['heures_travaillees'] or Decimal('0')
        self.montants['heures_supplementaires'] = heures['heures_sup'] or Decimal('0')
        
        # Récupérer les absences du mois
        absences = Absence.objects.filter(
            employe=self.employe,
            date_absence__gte=premier_jour,
            date_absence__lte=dernier_jour
        )
        
        jours_absence_non_paye = Decimal('0')
        jours_absence_total = Decimal('0')
        
        for absence in absences:
            jours_absence_total += absence.duree_jours
            if absence.impact_paie == 'non_paye':
                jours_absence_non_paye += absence.duree_jours
            elif absence.impact_paie == 'partiellement_paye':
                # Calculer la partie non payée
                taux_non_paye = (Decimal('100') - absence.taux_maintien_salaire) / Decimal('100')
                jours_absence_non_paye += absence.duree_jours * taux_non_paye
        
        self.montants['jours_absence'] = jours_absence_total
        self.montants['jours_absence_non_paye'] = jours_absence_non_paye
        
        # Récupérer les congés approuvés du mois
        conges = Conge.objects.filter(
            employe=self.employe,
            statut_demande='approuve',
            date_debut__lte=dernier_jour,
            date_fin__gte=premier_jour
        )
        
        jours_conge = Decimal('0')
        for conge in conges:
            # Calculer les jours de congé dans la période
            debut_conge = max(conge.date_debut, premier_jour)
            fin_conge = min(conge.date_fin, dernier_jour)
            jours_dans_periode = (fin_conge - debut_conge).days + 1
            jours_conge += Decimal(str(jours_dans_periode))
        
        self.montants['jours_conge'] = jours_conge
    
    def _appliquer_retenues_absences(self):
        """Appliquer les retenues pour absences non payées"""
        jours_absence_non_paye = self.montants.get('jours_absence_non_paye', Decimal('0'))
        
        if jours_absence_non_paye <= 0:
            return
        
        # Calculer le salaire journalier
        jours_ouvrables = self.montants['jours_ouvrables']
        if jours_ouvrables <= 0:
            jours_ouvrables = Decimal('22')  # Valeur par défaut
        
        salaire_journalier = self.montants['total_gains'] / jours_ouvrables
        
        # Calculer la retenue
        retenue = self._arrondir(salaire_journalier * jours_absence_non_paye)
        self.montants['retenue_absence'] = retenue
        
        # Ajouter la ligne de retenue
        rubrique_absence = RubriquePaie.objects.filter(
            code_rubrique__icontains='ABSENCE',
            type_rubrique='retenue',
            actif=True
        ).first()
        
        if rubrique_absence:
            self.lignes.append({
                'rubrique': rubrique_absence,
                'base': self.montants['total_gains'],
                'taux': Decimal('0'),
                'nombre': jours_absence_non_paye,
                'montant': retenue,
                'ordre': rubrique_absence.ordre_affichage
            })
    
    def _calculer_gains(self):
        """Calculer tous les éléments de gain"""
        # Récupérer les éléments de salaire de l'employé
        elements = ElementSalaire.objects.filter(
            employe=self.employe,
            actif=True,
            date_debut__lte=date(self.periode.annee, self.periode.mois, 1)
        ).filter(
            models.Q(date_fin__isnull=True) | 
            models.Q(date_fin__gte=date(self.periode.annee, self.periode.mois, 1))
        ).select_related('rubrique')
        
        for element in elements:
            if element.rubrique.type_rubrique == 'gain':
                montant = self._calculer_element(element)
                
                self.lignes.append({
                    'rubrique': element.rubrique,
                    'base': element.montant or Decimal('0'),
                    'taux': element.taux,
                    'nombre': Decimal('1'),
                    'montant': montant,
                    'ordre': element.rubrique.ordre_affichage
                })
                
                self.montants['total_gains'] += montant
                
                # Calculer les assiettes
                if element.rubrique.soumis_cnss:
                    self.montants['cnss_base'] += montant
                if element.rubrique.soumis_irg:
                    self.montants['imposable'] += montant
        
        # Ajouter les heures supplémentaires si présentes
        self._calculer_heures_supplementaires()
        
        # Vérifier le plafond 25% des indemnités forfaitaires
        self._verifier_plafond_indemnites_forfaitaires()
    
    def _calculer_element(self, element):
        """Calculer le montant d'un élément"""
        if element.montant:
            return self._arrondir(element.montant)
        elif element.taux and element.base_calcul:
            base = self._obtenir_base_calcul(element.base_calcul)
            return self._arrondir(base * element.taux / Decimal('100'))
        return Decimal('0')
    
    def _obtenir_base_calcul(self, code_base):
        """Obtenir la base de calcul"""
        if code_base == 'SALAIRE_BASE':
            # Chercher le salaire de base
            element_base = ElementSalaire.objects.filter(
                employe=self.employe,
                rubrique__code_rubrique__icontains='SAL_BASE',
                actif=True
            ).first()
            return element_base.montant if element_base else Decimal('0')
        elif code_base == 'BRUT':
            return self.montants['brut']
        elif code_base == 'CNSS_BASE':
            return self.montants['cnss_base']
        return Decimal('0')
    
    def _calculer_heures_supplementaires(self):
        """
        Calculer la rémunération des heures supplémentaires selon le Code du Travail guinéen (Art. 221).
        
        Barème des majorations (Art. 221):
        - 4 premières HS/semaine: +30% (130% du taux horaire)
        - Au-delà 4 HS/semaine: +60% (160% du taux horaire)
        - Heures de nuit (20h-6h): +20% (120% du taux horaire)
        - Jour férié (jour): +60% (160% du taux horaire)
        - Jour férié (nuit): +100% (200% du taux horaire)
        
        Note: Les pointages doivent distinguer les types d'heures supplémentaires.
        Pour simplifier, on utilise les champs du modèle Pointage si disponibles,
        sinon on applique un taux moyen pondéré.
        """
        # Récupérer les différents types d'heures supplémentaires
        heures_sup_30 = self.montants.get('heures_sup_30', Decimal('0'))  # 4 premières HS/semaine
        heures_sup_60 = self.montants.get('heures_sup_60', Decimal('0'))  # Au-delà 4 HS/semaine
        heures_sup_nuit = self.montants.get('heures_sup_nuit', Decimal('0'))  # Nuit (20h-6h)
        heures_sup_ferie_jour = self.montants.get('heures_sup_ferie_jour', Decimal('0'))  # Jour férié (jour)
        heures_sup_ferie_nuit = self.montants.get('heures_sup_ferie_nuit', Decimal('0'))  # Jour férié (nuit)
        
        # Compatibilité avec anciens champs
        heures_sup_15 = self.montants.get('heures_sup_15', Decimal('0'))
        heures_sup_25 = self.montants.get('heures_sup_25', Decimal('0'))
        heures_sup_50 = self.montants.get('heures_sup_50', Decimal('0'))
        heures_sup_100 = self.montants.get('heures_sup_ferie', Decimal('0'))
        
        # Mapper les anciens champs vers les nouveaux si non renseignés
        if heures_sup_30 == 0 and heures_sup_15 > 0:
            heures_sup_30 = heures_sup_15
        if heures_sup_60 == 0 and heures_sup_25 > 0:
            heures_sup_60 = heures_sup_25
        if heures_sup_nuit == 0 and heures_sup_50 > 0:
            heures_sup_nuit = heures_sup_50
        if heures_sup_ferie_jour == 0 and heures_sup_100 > 0:
            heures_sup_ferie_jour = heures_sup_100
        
        # Total des heures supplémentaires (ancien champ pour compatibilité)
        heures_sup_total = self.montants.get('heures_supplementaires', Decimal('0'))
        
        # Si les heures détaillées ne sont pas disponibles, utiliser le total avec taux +60%
        if heures_sup_30 == 0 and heures_sup_60 == 0 and heures_sup_nuit == 0 and heures_sup_ferie_jour == 0 and heures_sup_ferie_nuit == 0:
            heures_sup_60 = heures_sup_total  # Par défaut, appliquer le taux +60%
        
        heures_total = heures_sup_30 + heures_sup_60 + heures_sup_nuit + heures_sup_ferie_jour + heures_sup_ferie_nuit
        if heures_total <= 0:
            return
        
        # Obtenir le salaire horaire de base
        salaire_base = self._obtenir_base_calcul('SALAIRE_BASE')
        heures_mensuelles = self.constantes.get('HEURES_MENSUELLES', Decimal('173.33'))
        
        if heures_mensuelles <= 0:
            heures_mensuelles = Decimal('173.33')  # 40h x 52 semaines / 12 mois
        
        salaire_horaire = salaire_base / heures_mensuelles
        
        # Taux des heures supplémentaires selon le Code du Travail guinéen (Art. 221)
        TAUX_HS_30 = self.constantes.get('TAUX_HS_4PREM', Decimal('130'))      # 4 premières HS: +30% (130%)
        TAUX_HS_60 = self.constantes.get('TAUX_HS_AUDELA', Decimal('160'))     # Au-delà 4 HS: +60% (160%)
        TAUX_HS_NUIT = self.constantes.get('TAUX_HS_NUIT', Decimal('120'))     # Nuit (20h-6h): +20% (120%)
        TAUX_HS_FERIE_J = self.constantes.get('TAUX_HS_FERIE_JOUR', Decimal('160'))  # Férié jour: +60% (160%)
        TAUX_HS_FERIE_N = self.constantes.get('TAUX_HS_FERIE_NUIT', Decimal('200'))  # Férié nuit: +100% (200%)
        
        # Calculer le montant pour chaque type d'heures supplémentaires
        montant_hs_30 = self._arrondir(salaire_horaire * heures_sup_30 * TAUX_HS_30 / Decimal('100'))
        montant_hs_60 = self._arrondir(salaire_horaire * heures_sup_60 * TAUX_HS_60 / Decimal('100'))
        montant_hs_nuit = self._arrondir(salaire_horaire * heures_sup_nuit * TAUX_HS_NUIT / Decimal('100'))
        montant_hs_ferie_j = self._arrondir(salaire_horaire * heures_sup_ferie_jour * TAUX_HS_FERIE_J / Decimal('100'))
        montant_hs_ferie_n = self._arrondir(salaire_horaire * heures_sup_ferie_nuit * TAUX_HS_FERIE_N / Decimal('100'))
        
        montant_hs_total = montant_hs_30 + montant_hs_60 + montant_hs_nuit + montant_hs_ferie_j + montant_hs_ferie_n
        
        if montant_hs_total > 0:
            self.montants['total_gains'] += montant_hs_total
            self.montants['montant_heures_sup'] = montant_hs_total
            self.montants['montant_hs_30'] = montant_hs_30
            self.montants['montant_hs_60'] = montant_hs_60
            self.montants['montant_hs_nuit'] = montant_hs_nuit
            self.montants['montant_hs_ferie_jour'] = montant_hs_ferie_j
            self.montants['montant_hs_ferie_nuit'] = montant_hs_ferie_n
            
            # Ajouter à la base CNSS et imposable
            self.montants['cnss_base'] += montant_hs_total
            self.montants['imposable'] += montant_hs_total
            
            # Ajouter les lignes pour chaque type d'heures supplémentaires
            rubrique_hs = RubriquePaie.objects.filter(
                code_rubrique__icontains='HS',
                type_rubrique='gain',
                actif=True
            ).first()
            
            if rubrique_hs:
                # Ligne récapitulative des heures supplémentaires
                taux_moyen = (montant_hs_total / (salaire_horaire * heures_total) * Decimal('100')) if heures_total > 0 else Decimal('0')
                
                self.lignes.append({
                    'rubrique': rubrique_hs,
                    'base': salaire_horaire,
                    'taux': self._arrondir(taux_moyen),
                    'nombre': heures_total,
                    'montant': montant_hs_total,
                    'ordre': rubrique_hs.ordre_affichage
                })
    
    def _verifier_plafond_indemnites_forfaitaires(self):
        """
        Vérifie le plafond de 25% pour les indemnités forfaitaires exonérées.
        
        Selon la législation guinéenne, les indemnités forfaitaires (logement, transport, panier)
        sont exonérées de RTS dans la limite de 25% du salaire brut.
        Au-delà, l'excédent est réintégré dans la base imposable RTS.
        
        FORMULE CORRECTE:
        -----------------
        Salaire brut = Salaire de base + Primes/Indemnités
        Plafond exonéré = 25% × Salaire brut
        Si Primes > Plafond → Excédent réintégré dans base RTS
        
        VÉRIFICATION MATHÉMATIQUE:
        Pour que les primes soient exactement au plafond:
        Primes = 25% × (Salaire de base + Primes)
        Primes = 0.25 × Salaire de base + 0.25 × Primes
        0.75 × Primes = 0.25 × Salaire de base
        Primes = 33.33% × Salaire de base
        → Pour respecter le plafond 25% du brut, les primes ne doivent pas dépasser ~33% du salaire de base.
        
        Rubriques concernées:
        - PRIME_TRANSPORT, ALLOC_TRANSPORT
        - ALLOC_LOGEMENT, IND_LOGEMENT
        - IND_REPAS, IND_REPAS_JOUR, PRIME_PANIER
        """
        # Codes des rubriques d'indemnités forfaitaires exonérées
        CODES_INDEMNITES_FORFAITAIRES = [
            'PRIME_TRANSPORT', 'ALLOC_TRANSPORT', 'TRANSPORT',
            'ALLOC_LOGEMENT', 'IND_LOGEMENT', 'LOGEMENT',
            'IND_REPAS', 'IND_REPAS_JOUR', 'PRIME_PANIER', 'PANIER', 'REPAS',
        ]
        
        # Taux plafond (25% du brut)
        TAUX_PLAFOND = self.constantes.get('PLAFOND_INDEMNITES_PCT', Decimal('25'))
        
        # Calculer le salaire de base (éléments non forfaitaires)
        salaire_base = Decimal('0')
        total_indemnites = Decimal('0')
        
        for ligne in self.lignes:
            code = ligne['rubrique'].code_rubrique.upper() if ligne['rubrique'].code_rubrique else ''
            # Vérifier si c'est une indemnité forfaitaire
            est_indemnite_forfaitaire = any(ind in code for ind in CODES_INDEMNITES_FORFAITAIRES)
            
            if est_indemnite_forfaitaire:
                total_indemnites += ligne['montant']
            else:
                # C'est un élément de salaire de base ou autre prime non forfaitaire
                if ligne['rubrique'].type_rubrique == 'gain':
                    salaire_base += ligne['montant']
        
        self.montants['indemnites_forfaitaires'] = total_indemnites
        self.montants['salaire_base_hors_indemnites'] = salaire_base
        
        # Salaire brut = Salaire de base + Indemnités forfaitaires
        salaire_brut = salaire_base + total_indemnites
        
        # Plafond exonéré = 25% × Salaire brut
        plafond = self._arrondir(salaire_brut * TAUX_PLAFOND / Decimal('100'))
        self.montants['plafond_indemnites'] = plafond
        
        # Calcul du ratio pour information
        # Pour info: primes max = 33.33% du salaire de base pour respecter le plafond
        ratio_max_base = Decimal('33.33')  # 25% / 75% = 33.33%
        primes_max_theorique = self._arrondir(salaire_base * ratio_max_base / Decimal('100'))
        self.montants['primes_max_theorique'] = primes_max_theorique
        
        # Vérifier le dépassement
        if total_indemnites > plafond:
            depassement = total_indemnites - plafond
            self.montants['depassement_plafond_indemnites'] = depassement
            
            # Réintégrer l'excédent dans la base imposable RTS
            self.montants['reintegration_base_imposable'] = depassement
            self.montants['imposable'] += depassement
            
            # Ajouter une alerte dans les montants
            self.montants['alerte_plafond_indemnites'] = (
                f"⚠️ Indemnités forfaitaires ({total_indemnites:,.0f} GNF) dépassent le plafond 25% "
                f"du brut ({plafond:,.0f} GNF). Excédent de {depassement:,.0f} GNF réintégré dans la base imposable RTS."
            )
            
            # Ajouter à la liste des alertes du bulletin
            if 'alertes' not in self.montants:
                self.montants['alertes'] = []
            self.montants['alertes'].append({
                'type': 'avertissement',
                'message': f"Plafond 25% indemnités forfaitaires dépassé: {total_indemnites:,.0f} GNF > {plafond:,.0f} GNF. "
                           f"Excédent {depassement:,.0f} GNF réintégré dans base RTS."
            })
        else:
            self.montants['depassement_plafond_indemnites'] = Decimal('0')
            self.montants['reintegration_base_imposable'] = Decimal('0')
            self.montants['alerte_plafond_indemnites'] = ''
    
    def _calculer_cotisations_sociales(self):
        """Calculer les cotisations sociales (CNSS, etc.)
        
        Règles CNSS Guinée:
        - Plancher: SMIG (550 000 GNF) - on cotise au minimum sur ce montant
        - Plafond: 2 500 000 GNF - on cotise au maximum sur ce montant
        - Taux employé: 5% (retraite 2.5% + assurance maladie 2.5%)
        - Taux employeur: 18% (prestations familiales 6% + AT/MP 4% + retraite 4% + maladie 4%)
        """
        # Convertir la base CNSS en GNF si nécessaire (les cotisations sociales sont toujours en GNF)
        base_cnss_gnf = self.montants['cnss_base']
        if self.devise_employe != self.devise_base:
            base_cnss_gnf = DeviseService.convertir_vers_gnf(
                self.montants['cnss_base'], 
                self.devise_employe, 
                self.date_conversion
            )
        
        # Récupérer plancher et plafond CNSS (en GNF)
        # Plancher = 550 000 GNF - assiette minimale de cotisation
        plancher_cnss = self.constantes.get('PLANCHER_CNSS', Decimal('550000'))
        # Plafond = 2 500 000 GNF - assiette maximale de cotisation
        plafond_cnss = self.constantes.get('PLAFOND_CNSS', Decimal('2500000'))
        
        # Appliquer plancher et plafond CNSS
        # IMPORTANT: Le plancher ne s'applique que si le salarié a effectivement travaillé
        # Si salaire brut = 0 ou très faible (< 10% du plancher), pas de cotisation CNSS
        # Sinon: Si salaire < plancher : on cotise sur le plancher
        #        Si plancher <= salaire <= plafond : on cotise sur le salaire réel
        #        Si salaire > plafond : on cotise sur le plafond
        seuil_minimum = plancher_cnss * Decimal('0.10')  # 10% du plancher = 55 000 GNF
        
        if base_cnss_gnf < seuil_minimum:
            # Pas de cotisation CNSS si le salaire est quasi nul (absence totale, congé sans solde)
            base_cnss_plafonnee = Decimal('0')
        else:
            base_cnss_plafonnee = max(min(base_cnss_gnf, plafond_cnss), plancher_cnss)
        
        # CNSS salarié (utiliser TAUX_CNSS_EMPLOYE au lieu de TAUX_CNSS_SALARIE)
        taux_cnss = self.constantes.get('TAUX_CNSS_EMPLOYE', Decimal('5.00'))
        cnss_employe = self._arrondir(base_cnss_plafonnee * taux_cnss / Decimal('100'))
        
        self.montants['cnss_employe'] = cnss_employe
        self.montants['total_retenues'] += cnss_employe
        
        # Ajouter ligne CNSS
        rubrique_cnss = RubriquePaie.objects.filter(
            code_rubrique__icontains='CNSS',
            type_rubrique='retenue',
            actif=True
        ).first()
        
        if rubrique_cnss:
            self.lignes.append({
                'rubrique': rubrique_cnss,
                'base': self.montants['cnss_base'],
                'taux': taux_cnss,
                'nombre': Decimal('1'),
                'montant': cnss_employe,
                'ordre': rubrique_cnss.ordre_affichage
            })
        
        # CNSS employeur (appliquer aussi le plafond)
        taux_cnss_pat = self.constantes.get('TAUX_CNSS_EMPLOYEUR', Decimal('18.00'))
        self.montants['cnss_employeur'] = self._arrondir(
            base_cnss_plafonnee * taux_cnss_pat / Decimal('100')
        )
        
        # Versement Forfaitaire (VF) - 6% de la masse salariale (charge patronale)
        taux_vf = self.constantes.get('TAUX_VF', Decimal('6.00'))
        self.montants['versement_forfaitaire'] = self._arrondir(
            self.montants['brut'] * taux_vf / Decimal('100')
        )
        
        # Taxe d'Apprentissage - 2% de la masse salariale (charge patronale) - CGI 2022
        taux_ta = self.constantes.get('TAUX_TA', Decimal('2.00'))
        self.montants['taxe_apprentissage'] = self._arrondir(
            self.montants['brut'] * taux_ta / Decimal('100')
        )
        
        # Total charges patronales
        self.montants['total_charges_patronales'] = (
            self.montants['cnss_employeur'] +
            self.montants['versement_forfaitaire'] +
            self.montants['taxe_apprentissage']
        )
        
        # Autres cotisations (mutuelle, retraite complémentaire, etc.)
        self._calculer_autres_cotisations()
    
    def _calculer_autres_cotisations(self):
        """Calculer les autres cotisations (mutuelle, retraite, etc.)"""
        # Récupérer les éléments de retenue de type cotisation
        elements_cotis = ElementSalaire.objects.filter(
            employe=self.employe,
            rubrique__type_rubrique='retenue',
            rubrique__code_rubrique__in=[
                'RETRAITE_COMPL_SAL', 'ASSUR_SANTE_COMPL',
                'FONDS_SOLID_TELECOM', 'COTIS_SYNDICAT_PROG',
                'MUTUELLE_ENT'
            ],
            actif=True
        ).select_related('rubrique')
        
        for element in elements_cotis:
            montant = self._calculer_element(element)
            
            self.lignes.append({
                'rubrique': element.rubrique,
                'base': self.montants['cnss_base'],
                'taux': element.taux,
                'nombre': Decimal('1'),
                'montant': montant,
                'ordre': element.rubrique.ordre_affichage
            })
            
            self.montants['total_retenues'] += montant
    
    def _calculer_irg(self):
        """Calculer l'IRG/RTS selon le barème progressif"""
        # Base imposable = imposable - CNSS - autres déductions
        base_imposable = self.montants['imposable'] - self.montants['cnss_employe']
        
        # Convertir en GNF si nécessaire (la RTS est toujours calculée en GNF)
        if self.devise_employe != self.devise_base:
            base_imposable = DeviseService.convertir_vers_gnf(
                base_imposable, 
                self.devise_employe, 
                self.date_conversion
            )
        
        # Vérifier exonération RTS pour stagiaires/apprentis
        exoneration_rts, raison_exoneration = self._verifier_exoneration_rts_stagiaire()
        
        if exoneration_rts:
            # Stagiaire/apprenti exonéré de RTS
            self.montants['irg'] = Decimal('0')
            self.montants['exoneration_rts'] = True
            self.montants['raison_exoneration_rts'] = raison_exoneration
        else:
            # Appliquer déductions familiales
            deductions = self._calculer_deductions_familiales()
            base_imposable -= deductions
            
            # Appliquer abattements professionnels
            abattement = self._calculer_abattement_professionnel(base_imposable)
            base_imposable -= abattement
            
            # Calculer RTS progressif
            irg_brut = self._calculer_irg_progressif(base_imposable)
            
            # Appliquer crédits d'impôt
            credits = self._calculer_credits_impot()
            irg_net = max(Decimal('0'), irg_brut - credits)
            
            self.montants['irg'] = self._arrondir(irg_net)
            self.montants['exoneration_rts'] = False
        self.montants['total_retenues'] += self.montants['irg']
        
        # Ajouter ligne IRG
        rubrique_irg = RubriquePaie.objects.filter(
            code_rubrique__icontains='IRS',
            type_rubrique='retenue',
            actif=True
        ).first()
        
        if rubrique_irg:
            self.lignes.append({
                'rubrique': rubrique_irg,
                'base': base_imposable,
                'taux': None,
                'nombre': Decimal('1'),
                'montant': self.montants['irg'],
                'ordre': rubrique_irg.ordre_affichage
            })
    
    def _verifier_exoneration_rts_stagiaire(self):
        """
        Vérifie si l'employé est éligible à l'exonération RTS pour stagiaires/apprentis.
        
        Conditions (législation guinéenne):
        - Type de contrat: Stage ou Apprentissage
        - Durée: Maximum 12 mois depuis le début du contrat
        - Indemnité: ≤ 1 200 000 GNF/mois
        
        Returns:
            tuple: (exonere: bool, raison: str)
        """
        from datetime import date
        
        # Seuil d'exonération pour stagiaires/apprentis (depuis constantes ou défaut)
        SEUIL_EXONERATION = self.constantes.get('SEUIL_EXON_STAGIAIRE', Decimal('1200000'))
        
        # Vérifier si l'employé est stagiaire ou apprenti
        if not hasattr(self.employe, 'est_stagiaire_ou_apprenti') or not self.employe.est_stagiaire_ou_apprenti:
            return False, "Non stagiaire/apprenti"
        
        # Vérifier l'éligibilité (durée max 12 mois)
        date_calcul = date(self.periode.annee, self.periode.mois, 1)
        eligible, raison = self.employe.est_eligible_exoneration_rts(date_calcul)
        
        if not eligible:
            return False, raison
        
        # Vérifier le montant de l'indemnité (≤ 1 200 000 GNF)
        salaire_brut = self.montants['brut']
        
        # Convertir en GNF si nécessaire
        if self.devise_employe != self.devise_base:
            salaire_brut = DeviseService.convertir_vers_gnf(
                salaire_brut, 
                self.devise_employe, 
                self.date_conversion
            )
        
        if salaire_brut > SEUIL_EXONERATION:
            return False, f"Indemnité {salaire_brut:,.0f} GNF > seuil {SEUIL_EXONERATION:,.0f} GNF"
        
        return True, f"Exonéré RTS: {raison} - Indemnité ≤ {SEUIL_EXONERATION:,.0f} GNF"
    
    def _calculer_deductions_familiales(self):
        """Calculer les déductions familiales selon la législation guinéenne"""
        deductions = Decimal('0')
        
        # Conjoint (déduction pour personne mariée)
        if self.employe.situation_matrimoniale in ['marie', 'Marié(e)', 'Marié', 'Marié']:
            deduction_conjoint = self.constantes.get('DEDUC_CONJOINT', Decimal('100000'))
            deductions += deduction_conjoint
        
        # Enfants à charge (max 4 enfants en Guinée)
        if self.employe.nombre_enfants:
            max_enfants = int(self.constantes.get('MAX_ENFANTS_DEDUC', Decimal('4')))
            nb_enfants = min(self.employe.nombre_enfants, max_enfants)
            
            deduction_enfant = self.constantes.get('DEDUC_ENFANT', Decimal('50000'))
            deductions += deduction_enfant * nb_enfants
        
        return deductions
    
    def _calculer_abattement_professionnel(self, base):
        """Calculer l'abattement professionnel (5% plafonné)"""
        taux_abattement = Decimal('5.00')
        plafond = Decimal('1000000')
        
        abattement = base * taux_abattement / Decimal('100')
        return min(abattement, plafond)
    
    def _calculer_irg_progressif(self, base_imposable):
        """Calculer l'IRG selon le barème progressif"""
        if base_imposable <= 0:
            return Decimal('0')
        
        irg_total = Decimal('0')
        reste = base_imposable
        
        for tranche in self.tranches_irg:
            if reste <= 0:
                break
            
            # Montant de la tranche
            if tranche.borne_superieure:
                montant_tranche = min(
                    reste,
                    tranche.borne_superieure - tranche.borne_inferieure
                )
            else:
                montant_tranche = reste
            
            # IRG de la tranche
            irg_tranche = montant_tranche * tranche.taux_irg / Decimal('100')
            irg_total += irg_tranche
            
            reste -= montant_tranche
        
        return self._arrondir(irg_total)
    
    def _calculer_credits_impot(self):
        """Calculer les crédits d'impôt"""
        # Pour l'instant, retourner 0
        # À implémenter selon les besoins (formation, épargne retraite, etc.)
        return Decimal('0')
    
    def _calculer_autres_retenues(self):
        """Calculer les autres retenues (avances, prêts, etc.)"""
        # Récupérer les éléments de retenue non-cotisation
        elements_retenues = ElementSalaire.objects.filter(
            employe=self.employe,
            rubrique__type_rubrique='retenue',
            rubrique__code_rubrique__in=[
                'AVANCE_SAL', 'AVANCE_SAL_REGUL', 'RET_SYNDICAT',
                'PRET_LOGEMENT', 'PRET_LOGEMENT_REMBOURS',
                'RET_DISCIPLINAIRE', 'RET_DISCIPL_LEGER',
                'COTIS_ORDRE_PROF', 'EPARGNE_RETRAITE_VOL',
                'PLAN_EPARGNE_SAL', 'MUTUELLE_SUPP_VOL'
            ],
            actif=True
        ).select_related('rubrique')
        
        for element in elements_retenues:
            montant = element.montant or Decimal('0')
            
            self.lignes.append({
                'rubrique': element.rubrique,
                'base': montant,
                'taux': None,
                'nombre': Decimal('1'),
                'montant': montant,
                'ordre': element.rubrique.ordre_affichage
            })
            
            self.montants['total_retenues'] += montant
    
    @transaction.atomic
    def generer_bulletin(self, utilisateur=None):
        """Générer le bulletin de paie dans la base de données"""
        # Calculer le bulletin
        self.calculer_bulletin()
        
        # Générer le numéro de bulletin
        numero = self._generer_numero_bulletin()
        
        # Créer le bulletin
        bulletin = BulletinPaie.objects.create(
            employe=self.employe,
            periode=self.periode,
            numero_bulletin=numero,
            mois_paie=self.periode.mois,
            annee_paie=self.periode.annee,
            salaire_brut=self.montants['brut'],
            cnss_employe=self.montants['cnss_employe'],
            irg=self.montants['irg'],
            net_a_payer=self.montants['net'],
            cnss_employeur=self.montants['cnss_employeur'],
            devise_bulletin=self.devise_employe,
            statut_bulletin='calcule',
            date_calcul=timezone.now()
        )
        
        # Créer les lignes
        for ligne_data in sorted(self.lignes, key=lambda x: x['ordre']):
            LigneBulletin.objects.create(
                bulletin=bulletin,
                rubrique=ligne_data['rubrique'],
                base=ligne_data['base'],
                taux=ligne_data['taux'],
                nombre=ligne_data['nombre'],
                montant=ligne_data['montant'],
                ordre=ligne_data['ordre']
            )
        
        # Mettre à jour les cumuls
        self._mettre_a_jour_cumuls(bulletin)
        
        # Historique
        HistoriquePaie.objects.create(
            bulletin=bulletin,
            periode=self.periode,
            employe=self.employe,
            type_action='creation',
            description=f'Création du bulletin {numero}',
            utilisateur=utilisateur,
            valeurs_apres={
                'brut': float(self.montants['brut']),
                'net': float(self.montants['net']),
                'irg': float(self.montants['irg']),
            }
        )
        
        return bulletin
    
    def _generer_numero_bulletin(self):
        """Générer un numéro unique de bulletin"""
        prefix = f"BUL-{self.periode.annee}-{self.periode.mois:02d}"
        count = BulletinPaie.objects.filter(
            annee_paie=self.periode.annee,
            mois_paie=self.periode.mois
        ).count() + 1
        return f"{prefix}-{count:04d}"
    
    def _mettre_a_jour_cumuls(self, bulletin):
        """Mettre à jour les cumuls annuels"""
        cumul, created = CumulPaie.objects.get_or_create(
            employe=self.employe,
            annee=self.periode.annee,
            defaults={
                'cumul_brut': Decimal('0'),
                'cumul_imposable': Decimal('0'),
                'cumul_net': Decimal('0'),
                'cumul_cnss_employe': Decimal('0'),
                'cumul_cnss_employeur': Decimal('0'),
                'cumul_irg': Decimal('0'),
                'nombre_bulletins': 0
            }
        )
        
        cumul.cumul_brut += bulletin.salaire_brut
        cumul.cumul_net += bulletin.net_a_payer
        cumul.cumul_cnss_employe += bulletin.cnss_employe
        cumul.cumul_cnss_employeur += bulletin.cnss_employeur
        cumul.cumul_irg += bulletin.irg
        cumul.nombre_bulletins += 1
        cumul.save()


# Import manquant
from django.db import models
