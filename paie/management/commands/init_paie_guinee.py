"""
Commande pour initialiser les paramètres de paie selon la législation guinéenne
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, datetime
from decimal import Decimal
from paie.models import ParametrePaie, Constante, TrancheIRG, Variable


class Command(BaseCommand):
    help = 'Initialise les paramètres de paie conformes à la législation guinéenne 2025'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🇬🇳 Initialisation des paramètres de paie Guinée...'))
        
        # 1. Créer les paramètres généraux
        self.creer_parametres_generaux()
        
        # 2. Créer les constantes
        self.creer_constantes()
        
        # 3. Créer les tranches IRG
        self.creer_tranches_irg()
        
        # 4. Créer les variables
        self.creer_variables()
        
        self.stdout.write(self.style.SUCCESS('✅ Initialisation terminée avec succès!'))

    def creer_parametres_generaux(self):
        """Créer les paramètres généraux de paie"""
        self.stdout.write('📋 Création des paramètres généraux...')
        
        aujourd_hui = date.today()
        
        param, created = ParametrePaie.objects.get_or_create(
            mois_en_cours=aujourd_hui.month,
            annee_en_cours=aujourd_hui.year,
            defaults={
                'date_debut_periode': date(aujourd_hui.year, aujourd_hui.month, 1),
                'date_fin_periode': date(aujourd_hui.year, aujourd_hui.month, 28),
                'regulation_active': True,
                'plafond_abattement_irg': Decimal('300000'),
                'taux_abattement_irg': Decimal('20.00'),
                'type_bulletin_defaut': 'standard',
                'type_paiement_defaut': 'virement',
                'nombre_max_rubriques': 100,
                'acompte_regulier_actif': True,
                'acompte_exceptionnel_actif': True,
                'montant_max_acompte_pct': Decimal('50.00'),
                'devise': 'GNF',
                'suppression_auto_non_presents': False,
                'conserver_historique_admin': True,
                'duree_conservation_mois': 120,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ Paramètres généraux créés'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠ Paramètres généraux déjà existants'))

    def creer_constantes(self):
        """Créer les constantes de paie guinéennes"""
        self.stdout.write('💰 Création des constantes...')
        
        constantes = [
            # SMIG
            {
                'code': 'SMIG',
                'libelle': 'Salaire Minimum Interprofessionnel Garanti',
                'valeur': Decimal('440000'),
                'type_valeur': 'montant',
                'categorie': 'general',
                'unite': 'GNF',
                'description': 'SMIG mensuel en Guinée (2025)'
            },
            
            # CNSS
            {
                'code': 'PLAFOND_CNSS',
                'libelle': 'Plafond de cotisation CNSS',
                'valeur': Decimal('2500000'),
                'type_valeur': 'montant',
                'categorie': 'cnss',
                'unite': 'GNF',
                'description': 'Plafond mensuel pour le calcul des cotisations CNSS (2 500 000 GNF)'
            },
            {
                'code': 'PLANCHER_CNSS',
                'libelle': 'Plancher de cotisation CNSS (SMIG)',
                'valeur': Decimal('440000'),
                'type_valeur': 'montant',
                'categorie': 'cnss',
                'unite': 'GNF',
                'description': 'Plancher mensuel = SMIG (440 000 GNF) - assiette minimale de cotisation'
            },
            {
                'code': 'TAUX_CNSS_EMPLOYE',
                'libelle': 'Taux CNSS part employé',
                'valeur': Decimal('5.00'),
                'type_valeur': 'pourcentage',
                'categorie': 'cnss',
                'unite': '%',
                'description': 'Part employé de la cotisation CNSS'
            },
            {
                'code': 'TAUX_CNSS_EMPLOYEUR',
                'libelle': 'Taux CNSS part employeur',
                'valeur': Decimal('18.00'),
                'type_valeur': 'pourcentage',
                'categorie': 'cnss',
                'unite': '%',
                'description': 'Part employeur de la cotisation CNSS'
            },
            
            # INAM
            {
                'code': 'PLAFOND_INAM',
                'libelle': 'Plafond de cotisation INAM',
                'valeur': Decimal('3000000'),
                'type_valeur': 'montant',
                'categorie': 'inam',
                'unite': 'GNF',
                'description': 'Plafond mensuel pour le calcul INAM'
            },
            {
                'code': 'TAUX_INAM',
                'libelle': 'Taux INAM',
                'valeur': Decimal('2.50'),
                'type_valeur': 'pourcentage',
                'categorie': 'inam',
                'unite': '%',
                'description': 'Taux de cotisation INAM'
            },
            
            # Temps de travail
            {
                'code': 'JOURS_MOIS',
                'libelle': 'Nombre de jours ouvrables par mois',
                'valeur': Decimal('22'),
                'type_valeur': 'nombre',
                'categorie': 'temps',
                'unite': 'jours',
                'description': 'Nombre moyen de jours travaillés par mois'
            },
            {
                'code': 'HEURES_MOIS',
                'libelle': 'Nombre d\'heures par mois',
                'valeur': Decimal('173.33'),
                'type_valeur': 'nombre',
                'categorie': 'temps',
                'unite': 'heures',
                'description': 'Nombre d\'heures mensuelles (40h/semaine)'
            },
            {
                'code': 'CONGES_ANNUELS',
                'libelle': 'Congés annuels légaux',
                'valeur': Decimal('26'),
                'type_valeur': 'nombre',
                'categorie': 'temps',
                'unite': 'jours',
                'description': 'Nombre de jours de congés annuels selon Code du Travail'
            },
        ]
        
        for const_data in constantes:
            const, created = Constante.objects.get_or_create(
                code=const_data['code'],
                defaults={
                    **const_data,
                    'date_debut_validite': date(2025, 1, 1),
                    'actif': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ {const_data["code"]}: {const_data["valeur"]} {const_data["unite"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠ {const_data["code"]} déjà existant'))

    def creer_tranches_irg(self):
        """Créer les tranches du barème IRG 2025"""
        self.stdout.write('📊 Création des tranches IRG...')
        
        tranches = [
            {
                'numero_tranche': 1,
                'borne_inferieure': Decimal('0'),
                'borne_superieure': Decimal('1000000'),
                'taux_irg': Decimal('0.00'),
            },
            {
                'numero_tranche': 2,
                'borne_inferieure': Decimal('1000001'),
                'borne_superieure': Decimal('3000000'),
                'taux_irg': Decimal('5.00'),
            },
            {
                'numero_tranche': 3,
                'borne_inferieure': Decimal('3000001'),
                'borne_superieure': Decimal('6000000'),
                'taux_irg': Decimal('10.00'),
            },
            {
                'numero_tranche': 4,
                'borne_inferieure': Decimal('6000001'),
                'borne_superieure': Decimal('12000000'),
                'taux_irg': Decimal('15.00'),
            },
            {
                'numero_tranche': 5,
                'borne_inferieure': Decimal('12000001'),
                'borne_superieure': Decimal('25000000'),
                'taux_irg': Decimal('20.00'),
            },
            {
                'numero_tranche': 6,
                'borne_inferieure': Decimal('25000001'),
                'borne_superieure': None,  # Illimité
                'taux_irg': Decimal('25.00'),
            },
        ]
        
        for tranche_data in tranches:
            tranche, created = TrancheIRG.objects.get_or_create(
                annee_validite=2025,
                numero_tranche=tranche_data['numero_tranche'],
                defaults={
                    **tranche_data,
                    'date_debut_validite': date(2025, 1, 1),
                    'actif': True
                }
            )
            if created:
                if tranche_data['borne_superieure']:
                    self.stdout.write(self.style.SUCCESS(
                        f'  ✓ Tranche {tranche_data["numero_tranche"]}: '
                        f'{tranche_data["borne_inferieure"]:,.0f} - {tranche_data["borne_superieure"]:,.0f} GNF '
                        f'({tranche_data["taux_irg"]}%)'
                    ))
                else:
                    self.stdout.write(self.style.SUCCESS(
                        f'  ✓ Tranche {tranche_data["numero_tranche"]}: '
                        f'> {tranche_data["borne_inferieure"]:,.0f} GNF '
                        f'({tranche_data["taux_irg"]}%)'
                    ))
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠ Tranche {tranche_data["numero_tranche"]} déjà existante'))

    def creer_variables(self):
        """Créer les variables de paie"""
        self.stdout.write('🔢 Création des variables...')
        
        variables = [
            {
                'code': 'JOURS_PAYES',
                'libelle': 'Nombre de jours payés',
                'type_variable': 'numerique',
                'portee': 'employe',
                'valeur_defaut': '22',
                'description': 'Nombre de jours travaillés et payés dans le mois'
            },
            {
                'code': 'HEURES_SUP',
                'libelle': 'Heures supplémentaires',
                'type_variable': 'numerique',
                'portee': 'employe',
                'valeur_defaut': '0',
                'description': 'Nombre d\'heures supplémentaires effectuées'
            },
            {
                'code': 'TAUX_PRESENCE',
                'libelle': 'Taux de présence',
                'type_variable': 'numerique',
                'portee': 'employe',
                'valeur_defaut': '100',
                'description': 'Taux de présence en % pour le mois'
            },
        ]
        
        for var_data in variables:
            var, created = Variable.objects.get_or_create(
                code=var_data['code'],
                defaults={
                    **var_data,
                    'actif': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ {var_data["code"]}: {var_data["libelle"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠ {var_data["code"]} déjà existante'))
