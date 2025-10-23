"""
Services de calcul de paie
Moteur de calcul automatique conforme à la législation guinéenne
"""
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from django.db import transaction
from django.utils import timezone

from .models import (
    BulletinPaie, LigneBulletin, ElementSalaire, CumulPaie,
    RubriquePaie, Constante, TrancheIRG, PeriodePaie, HistoriquePaie
)
from employes.models import Employe


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
        }
        self.constantes = self._charger_constantes()
        self.tranches_irg = self._charger_tranches_irg()
    
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
        
        # 1. Calculer les gains
        self._calculer_gains()
        
        # 2. Calculer le brut
        self.montants['brut'] = self.montants['total_gains']
        
        # 3. Calculer les cotisations sociales
        self._calculer_cotisations_sociales()
        
        # 4. Calculer l'IRG/IRSA
        self._calculer_irg()
        
        # 5. Calculer les autres retenues
        self._calculer_autres_retenues()
        
        # 6. Calculer le net
        self.montants['net'] = (
            self.montants['brut'] - 
            self.montants['total_retenues']
        )
        
        return self.montants
    
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
    
    def _calculer_cotisations_sociales(self):
        """Calculer les cotisations sociales (CNSS, etc.)"""
        # CNSS salarié
        taux_cnss = self.constantes.get('TAUX_CNSS_SALARIE', Decimal('5.50'))
        cnss_employe = self._arrondir(self.montants['cnss_base'] * taux_cnss / Decimal('100'))
        
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
        
        # CNSS employeur
        taux_cnss_pat = self.constantes.get('TAUX_CNSS_EMPLOYEUR', Decimal('18.00'))
        self.montants['cnss_employeur'] = self._arrondir(
            self.montants['cnss_base'] * taux_cnss_pat / Decimal('100')
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
        """Calculer l'IRG/IRSA selon le barème progressif"""
        # Base imposable = imposable - CNSS - autres déductions
        base_imposable = self.montants['imposable'] - self.montants['cnss_employe']
        
        # Appliquer déductions familiales
        deductions = self._calculer_deductions_familiales()
        base_imposable -= deductions
        
        # Appliquer abattements professionnels
        abattement = self._calculer_abattement_professionnel(base_imposable)
        base_imposable -= abattement
        
        # Calculer IRG progressif
        irg_brut = self._calculer_irg_progressif(base_imposable)
        
        # Appliquer crédits d'impôt
        credits = self._calculer_credits_impot()
        irg_net = max(Decimal('0'), irg_brut - credits)
        
        self.montants['irg'] = self._arrondir(irg_net)
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
    
    def _calculer_deductions_familiales(self):
        """Calculer les déductions familiales"""
        deductions = Decimal('0')
        
        # Conjoint
        if self.employe.situation_matrimoniale in ['Marié(e)', 'Marié']:
            deduction_conjoint = self.constantes.get('DEDUC_CONJOINT_EXPERT', Decimal('100000'))
            if not deduction_conjoint:
                deduction_conjoint = self.constantes.get('DEDUC_CONJOINT', Decimal('50000'))
            deductions += deduction_conjoint
        
        # Enfants à charge
        if self.employe.nombre_enfants:
            max_enfants = int(self.constantes.get('MAX_ENFANTS_DEDUC', Decimal('3')))
            nb_enfants = min(self.employe.nombre_enfants, max_enfants)
            
            deduction_enfant = self.constantes.get('DEDUC_ENFANT_LOCAL', Decimal('100000'))
            if not deduction_enfant:
                deduction_enfant = self.constantes.get('DEDUC_ENFANT', Decimal('75000'))
            
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
