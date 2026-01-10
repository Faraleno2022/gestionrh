"""
Commande pour créer les données de test du module comptabilité
Plan comptable OHADA simplifié, journaux, exercice et écritures
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from comptabilite.models import (
    PlanComptable, Journal, ExerciceComptable, EcritureComptable, LigneEcriture, 
    Tiers, Facture, LigneFacture, Reglement
)
from core.models import Entreprise


class Command(BaseCommand):
    help = 'Crée les données de test pour le module comptabilité'

    def add_arguments(self, parser):
        parser.add_argument(
            '--entreprise',
            type=str,
            help='ID (UUID) de l\'entreprise (utilise la première si non spécifié)'
        )

    def handle(self, *args, **options):
        entreprise_id = options.get('entreprise')
        
        if entreprise_id:
            entreprise = Entreprise.objects.get(pk=entreprise_id)
        else:
            entreprise = Entreprise.objects.first()
        
        if not entreprise:
            self.stdout.write(self.style.ERROR('Aucune entreprise trouvée'))
            return
        
        self.stdout.write(f'Création des données pour: {entreprise.nom_entreprise}')
        
        # 1. Créer le plan comptable OHADA
        self.creer_plan_comptable(entreprise)
        
        # 2. Créer les journaux
        self.creer_journaux(entreprise)
        
        # 3. Créer l'exercice comptable
        exercice = self.creer_exercice(entreprise)
        
        # 4. Créer les tiers
        self.creer_tiers(entreprise)
        
        # 5. Créer des écritures de test
        self.creer_ecritures(entreprise, exercice)
        
        # 6. Créer des factures impayées
        self.creer_factures(entreprise)
        
        # 7. Créer des règlements
        self.creer_reglements(entreprise)
        
        self.stdout.write(self.style.SUCCESS('Données de test créées avec succès!'))

    def creer_plan_comptable(self, entreprise):
        """Créer le plan comptable OHADA simplifié"""
        
        # Vérifier si déjà créé
        if PlanComptable.objects.filter(entreprise=entreprise).exists():
            self.stdout.write('  Plan comptable déjà existant, ignoré')
            return
        
        comptes = [
            # Classe 1 - Capitaux
            ('1', '10', '101000', 'Capital social'),
            ('1', '10', '106000', 'Réserves'),
            ('1', '11', '110000', 'Report à nouveau'),
            ('1', '12', '120000', 'Résultat de l\'exercice'),
            ('1', '16', '162000', 'Emprunts bancaires'),
            
            # Classe 2 - Immobilisations
            ('2', '21', '211000', 'Terrains'),
            ('2', '21', '213000', 'Constructions'),
            ('2', '21', '215000', 'Installations techniques'),
            ('2', '22', '221000', 'Terrains en concession'),
            ('2', '24', '241000', 'Matériel de transport'),
            ('2', '24', '244000', 'Mobilier et matériel de bureau'),
            ('2', '24', '245000', 'Matériel informatique'),
            ('2', '28', '281300', 'Amort. constructions'),
            ('2', '28', '284400', 'Amort. matériel de bureau'),
            ('2', '28', '284500', 'Amort. matériel informatique'),
            
            # Classe 3 - Stocks
            ('3', '31', '311000', 'Marchandises'),
            ('3', '32', '321000', 'Matières premières'),
            ('3', '33', '331000', 'Produits en cours'),
            ('3', '35', '351000', 'Produits finis'),
            ('3', '39', '391000', 'Dépréciation des stocks'),
            
            # Classe 4 - Tiers
            ('4', '40', '401000', 'Fournisseurs'),
            ('4', '40', '401100', 'Fournisseurs - effets à payer'),
            ('4', '40', '408000', 'Fournisseurs - factures non parvenues'),
            ('4', '41', '411000', 'Clients'),
            ('4', '41', '411100', 'Clients - effets à recevoir'),
            ('4', '41', '416000', 'Clients douteux'),
            ('4', '41', '418000', 'Clients - produits à recevoir'),
            ('4', '42', '421000', 'Personnel - rémunérations dues'),
            ('4', '42', '422000', 'Personnel - acomptes et avances'),
            ('4', '43', '431000', 'CNSS'),
            ('4', '43', '432000', 'Autres organismes sociaux'),
            ('4', '44', '441000', 'État - impôt sur les bénéfices'),
            ('4', '44', '443000', 'État - TVA collectée'),
            ('4', '44', '445000', 'État - TVA déductible'),
            ('4', '44', '447000', 'État - RTS'),
            ('4', '46', '462000', 'Créances sur cessions d\'immobilisations'),
            ('4', '47', '471000', 'Compte d\'attente'),
            ('4', '48', '481000', 'Charges à répartir'),
            
            # Classe 5 - Trésorerie
            ('5', '52', '521000', 'Banque compte courant'),
            ('5', '52', '522000', 'Banque compte épargne'),
            ('5', '53', '531000', 'Caisse siège'),
            ('5', '53', '532000', 'Caisse agence'),
            ('5', '58', '581000', 'Virements internes'),
            
            # Classe 6 - Charges
            ('6', '60', '601000', 'Achats de marchandises'),
            ('6', '60', '602000', 'Achats de matières premières'),
            ('6', '60', '604000', 'Achats de services'),
            ('6', '60', '605000', 'Achats de fournitures'),
            ('6', '61', '611000', 'Transports sur achats'),
            ('6', '61', '612000', 'Transports sur ventes'),
            ('6', '61', '613000', 'Locations'),
            ('6', '61', '614000', 'Charges locatives'),
            ('6', '62', '621000', 'Sous-traitance'),
            ('6', '62', '622000', 'Honoraires'),
            ('6', '62', '624000', 'Publicité'),
            ('6', '62', '625000', 'Déplacements et missions'),
            ('6', '62', '626000', 'Frais postaux et télécommunications'),
            ('6', '62', '627000', 'Services bancaires'),
            ('6', '63', '631000', 'Frais bancaires'),
            ('6', '64', '641000', 'Impôts et taxes'),
            ('6', '64', '645000', 'Droits d\'enregistrement'),
            ('6', '66', '661000', 'Salaires et traitements'),
            ('6', '66', '662000', 'Primes et gratifications'),
            ('6', '66', '663000', 'Indemnités et avantages'),
            ('6', '66', '664000', 'Charges sociales'),
            ('6', '66', '668000', 'Autres charges de personnel'),
            ('6', '67', '671000', 'Intérêts des emprunts'),
            ('6', '67', '674000', 'Frais financiers'),
            ('6', '68', '681000', 'Dotations aux amortissements'),
            ('6', '68', '684000', 'Dotations aux provisions'),
            ('6', '69', '691000', 'Impôt sur les bénéfices'),
            
            # Classe 7 - Produits
            ('7', '70', '701000', 'Ventes de marchandises'),
            ('7', '70', '702000', 'Ventes de produits finis'),
            ('7', '70', '704000', 'Travaux'),
            ('7', '70', '705000', 'Études'),
            ('7', '70', '706000', 'Prestations de services'),
            ('7', '70', '707000', 'Produits accessoires'),
            ('7', '71', '711000', 'Subventions d\'exploitation'),
            ('7', '72', '721000', 'Production immobilisée'),
            ('7', '75', '751000', 'Produits des participations'),
            ('7', '75', '754000', 'Revenus des créances'),
            ('7', '76', '761000', 'Produits financiers'),
            ('7', '77', '771000', 'Produits exceptionnels'),
            ('7', '78', '781000', 'Reprises sur amortissements'),
            ('7', '78', '784000', 'Reprises sur provisions'),
        ]
        
        for classe, sous_classe, numero, intitule in comptes:
            PlanComptable.objects.create(
                entreprise=entreprise,
                numero_compte=numero,
                intitule=intitule,
                classe=classe,
                est_actif=True
            )
        
        self.stdout.write(f'  {len(comptes)} comptes créés')

    def creer_journaux(self, entreprise):
        """Créer les journaux comptables"""
        
        if Journal.objects.filter(entreprise=entreprise).exists():
            self.stdout.write('  Journaux déjà existants, ignoré')
            return
        
        # Récupérer les comptes de contrepartie
        compte_banque = PlanComptable.objects.filter(
            entreprise=entreprise, numero_compte='521000'
        ).first()
        compte_caisse = PlanComptable.objects.filter(
            entreprise=entreprise, numero_compte='531000'
        ).first()
        
        journaux = [
            ('AC', 'Journal des achats', 'achat', None),
            ('VT', 'Journal des ventes', 'vente', None),
            ('BQ', 'Journal de banque', 'banque', compte_banque),
            ('CA', 'Journal de caisse', 'caisse', compte_caisse),
            ('OD', 'Journal des opérations diverses', 'od', None),
            ('AN', 'Journal des à-nouveaux', 'an', None),
            ('SA', 'Journal des salaires', 'od', None),
        ]
        
        for code, libelle, type_j, contrepartie in journaux:
            Journal.objects.create(
                entreprise=entreprise,
                code=code,
                libelle=libelle,
                type_journal=type_j,
                compte_contrepartie=contrepartie,
                est_actif=True
            )
        
        self.stdout.write(f'  {len(journaux)} journaux créés')

    def creer_exercice(self, entreprise):
        """Créer l'exercice comptable"""
        
        exercice = ExerciceComptable.objects.filter(
            entreprise=entreprise, est_courant=True
        ).first()
        
        if exercice:
            self.stdout.write('  Exercice courant déjà existant')
            return exercice
        
        annee = timezone.now().year
        exercice = ExerciceComptable.objects.create(
            entreprise=entreprise,
            libelle=f'Exercice {annee}',
            date_debut=date(annee, 1, 1),
            date_fin=date(annee, 12, 31),
            statut='ouvert',
            est_courant=True
        )
        
        self.stdout.write(f'  Exercice {annee} créé')
        return exercice

    def creer_tiers(self, entreprise):
        """Créer des tiers de test"""
        
        if Tiers.objects.filter(entreprise=entreprise).exists():
            self.stdout.write('  Tiers déjà existants, ignoré')
            return
        
        compte_client = PlanComptable.objects.filter(
            entreprise=entreprise, numero_compte='411000'
        ).first()
        compte_fournisseur = PlanComptable.objects.filter(
            entreprise=entreprise, numero_compte='401000'
        ).first()
        
        tiers_list = [
            ('CLI001', 'SOGUIPAH SA', 'client', compte_client, '123456789', 'Conakry, Guinée'),
            ('CLI002', 'SOBRAGUI', 'client', compte_client, '987654321', 'Conakry, Guinée'),
            ('CLI003', 'SOCIÉTÉ MINIÈRE DE GUINÉE', 'client', compte_client, '456789123', 'Kamsar, Guinée'),
            ('FOU001', 'ORANGE GUINÉE', 'fournisseur', compte_fournisseur, '111222333', 'Kaloum, Conakry'),
            ('FOU002', 'EDG', 'fournisseur', compte_fournisseur, '444555666', 'Conakry, Guinée'),
            ('FOU003', 'PAPETERIE CENTRALE', 'fournisseur', compte_fournisseur, '777888999', 'Madina, Conakry'),
        ]
        
        for code, raison, type_t, compte, nif, adresse in tiers_list:
            Tiers.objects.create(
                entreprise=entreprise,
                code=code,
                raison_sociale=raison,
                type_tiers=type_t,
                compte_comptable=compte,
                nif=nif,
                adresse=adresse,
                est_actif=True
            )
        
        self.stdout.write(f'  {len(tiers_list)} tiers créés')

    def creer_ecritures(self, entreprise, exercice):
        """Créer des écritures de test"""
        
        if EcritureComptable.objects.filter(entreprise=entreprise).exists():
            self.stdout.write('  Écritures déjà existantes, ignoré')
            return
        
        # Récupérer les journaux et comptes
        journal_vente = Journal.objects.filter(entreprise=entreprise, code='VT').first()
        journal_achat = Journal.objects.filter(entreprise=entreprise, code='AC').first()
        journal_banque = Journal.objects.filter(entreprise=entreprise, code='BQ').first()
        journal_caisse = Journal.objects.filter(entreprise=entreprise, code='CA').first()
        journal_od = Journal.objects.filter(entreprise=entreprise, code='OD').first()
        journal_salaire = Journal.objects.filter(entreprise=entreprise, code='SA').first()
        
        def get_compte(numero):
            return PlanComptable.objects.filter(entreprise=entreprise, numero_compte=numero).first()
        
        today = timezone.now().date()
        
        ecritures_data = [
            # Ventes
            {
                'journal': journal_vente,
                'numero': 'VT-001',
                'date': today - timedelta(days=30),
                'libelle': 'Vente prestations SOGUIPAH',
                'lignes': [
                    (get_compte('411000'), 'Client SOGUIPAH', Decimal('15000000'), Decimal('0')),
                    (get_compte('706000'), 'Prestations de services', Decimal('0'), Decimal('15000000')),
                ]
            },
            {
                'journal': journal_vente,
                'numero': 'VT-002',
                'date': today - timedelta(days=25),
                'libelle': 'Vente marchandises SOBRAGUI',
                'lignes': [
                    (get_compte('411000'), 'Client SOBRAGUI', Decimal('8500000'), Decimal('0')),
                    (get_compte('701000'), 'Ventes marchandises', Decimal('0'), Decimal('8500000')),
                ]
            },
            # Achats
            {
                'journal': journal_achat,
                'numero': 'AC-001',
                'date': today - timedelta(days=28),
                'libelle': 'Achat fournitures bureau',
                'lignes': [
                    (get_compte('605000'), 'Fournitures de bureau', Decimal('2500000'), Decimal('0')),
                    (get_compte('401000'), 'Fournisseur PAPETERIE', Decimal('0'), Decimal('2500000')),
                ]
            },
            {
                'journal': journal_achat,
                'numero': 'AC-002',
                'date': today - timedelta(days=20),
                'libelle': 'Facture téléphone ORANGE',
                'lignes': [
                    (get_compte('626000'), 'Télécommunications', Decimal('1800000'), Decimal('0')),
                    (get_compte('401000'), 'Fournisseur ORANGE', Decimal('0'), Decimal('1800000')),
                ]
            },
            # Règlements clients
            {
                'journal': journal_banque,
                'numero': 'BQ-001',
                'date': today - timedelta(days=15),
                'libelle': 'Encaissement client SOGUIPAH',
                'lignes': [
                    (get_compte('521000'), 'Banque', Decimal('15000000'), Decimal('0')),
                    (get_compte('411000'), 'Client SOGUIPAH', Decimal('0'), Decimal('15000000')),
                ]
            },
            # Paiement fournisseurs
            {
                'journal': journal_banque,
                'numero': 'BQ-002',
                'date': today - timedelta(days=10),
                'libelle': 'Paiement ORANGE',
                'lignes': [
                    (get_compte('401000'), 'Fournisseur ORANGE', Decimal('1800000'), Decimal('0')),
                    (get_compte('521000'), 'Banque', Decimal('0'), Decimal('1800000')),
                ]
            },
            # Caisse
            {
                'journal': journal_caisse,
                'numero': 'CA-001',
                'date': today - timedelta(days=12),
                'libelle': 'Retrait banque pour caisse',
                'lignes': [
                    (get_compte('531000'), 'Caisse', Decimal('5000000'), Decimal('0')),
                    (get_compte('521000'), 'Banque', Decimal('0'), Decimal('5000000')),
                ]
            },
            {
                'journal': journal_caisse,
                'numero': 'CA-002',
                'date': today - timedelta(days=8),
                'libelle': 'Achat petit matériel',
                'lignes': [
                    (get_compte('605000'), 'Fournitures', Decimal('350000'), Decimal('0')),
                    (get_compte('531000'), 'Caisse', Decimal('0'), Decimal('350000')),
                ]
            },
            # Salaires
            {
                'journal': journal_salaire,
                'numero': 'SA-001',
                'date': today - timedelta(days=5),
                'libelle': 'Salaires décembre 2025',
                'lignes': [
                    (get_compte('661000'), 'Salaires bruts', Decimal('45000000'), Decimal('0')),
                    (get_compte('664000'), 'Charges sociales patronales', Decimal('8100000'), Decimal('0')),
                    (get_compte('421000'), 'Personnel - rémunérations dues', Decimal('0'), Decimal('38250000')),
                    (get_compte('431000'), 'CNSS', Decimal('0'), Decimal('10350000')),
                    (get_compte('447000'), 'État - RTS', Decimal('0'), Decimal('4500000')),
                ]
            },
            # Paiement salaires
            {
                'journal': journal_banque,
                'numero': 'BQ-003',
                'date': today - timedelta(days=3),
                'libelle': 'Virement salaires décembre',
                'lignes': [
                    (get_compte('421000'), 'Personnel', Decimal('38250000'), Decimal('0')),
                    (get_compte('521000'), 'Banque', Decimal('0'), Decimal('38250000')),
                ]
            },
            # OD - Dotation amortissement
            {
                'journal': journal_od,
                'numero': 'OD-001',
                'date': today - timedelta(days=2),
                'libelle': 'Dotation amortissement matériel informatique',
                'lignes': [
                    (get_compte('681000'), 'Dotations aux amortissements', Decimal('2000000'), Decimal('0')),
                    (get_compte('284500'), 'Amort. matériel informatique', Decimal('0'), Decimal('2000000')),
                ]
            },
        ]
        
        nb_ecritures = 0
        for data in ecritures_data:
            if not data['journal']:
                continue
            
            ecriture = EcritureComptable.objects.create(
                entreprise=entreprise,
                exercice=exercice,
                journal=data['journal'],
                numero_ecriture=data['numero'],
                date_ecriture=data['date'],
                libelle=data['libelle'],
                est_validee=True,
                date_validation=timezone.now()
            )
            
            for compte, libelle, debit, credit in data['lignes']:
                if compte:
                    LigneEcriture.objects.create(
                        ecriture=ecriture,
                        compte=compte,
                        libelle=libelle,
                        montant_debit=debit,
                        montant_credit=credit
                    )
            
            nb_ecritures += 1
        
        self.stdout.write(f'  {nb_ecritures} écritures créées')

    def creer_factures(self, entreprise):
        """Créer des factures impayées de test"""
        
        if Facture.objects.filter(entreprise=entreprise).exists():
            self.stdout.write('  Factures déjà existantes, ignoré')
            return
        
        today = timezone.now().date()
        
        # Récupérer les tiers
        clients = Tiers.objects.filter(entreprise=entreprise, type_tiers='client')
        fournisseurs = Tiers.objects.filter(entreprise=entreprise, type_tiers='fournisseur')
        
        # Récupérer les comptes pour les lignes
        compte_vente = PlanComptable.objects.filter(entreprise=entreprise, numero_compte='706000').first()
        compte_marchandises = PlanComptable.objects.filter(entreprise=entreprise, numero_compte='701000').first()
        compte_achat = PlanComptable.objects.filter(entreprise=entreprise, numero_compte='601000').first()
        compte_fournitures = PlanComptable.objects.filter(entreprise=entreprise, numero_compte='605000').first()
        
        factures_data = []
        
        # Factures de vente impayées (clients)
        for i, client in enumerate(clients[:3], 1):
            factures_data.append({
                'numero': f'FV-2026-{i:03d}',
                'type': 'vente',
                'tiers': client,
                'date_facture': today - timedelta(days=30-i*5),
                'date_echeance': today - timedelta(days=10-i*5),  # Certaines en retard
                'lignes': [
                    {'designation': 'Prestation de conseil', 'qte': 1, 'pu': Decimal('5000000'), 'compte': compte_vente},
                    {'designation': 'Formation personnel', 'qte': 2, 'pu': Decimal('2500000'), 'compte': compte_vente},
                ],
                'statut': 'validee',
            })
        
        # Factures d'achat impayées (fournisseurs)
        for i, fournisseur in enumerate(fournisseurs[:3], 1):
            factures_data.append({
                'numero': f'FA-2026-{i:03d}',
                'type': 'achat',
                'tiers': fournisseur,
                'date_facture': today - timedelta(days=25-i*5),
                'date_echeance': today + timedelta(days=5+i*5),  # À venir
                'lignes': [
                    {'designation': 'Fournitures de bureau', 'qte': 10, 'pu': Decimal('150000'), 'compte': compte_fournitures},
                    {'designation': 'Consommables informatiques', 'qte': 5, 'pu': Decimal('350000'), 'compte': compte_achat},
                ],
                'statut': 'validee',
            })
        
        nb_factures = 0
        for data in factures_data:
            # Calculer les montants
            montant_ht = Decimal('0')
            for ligne in data['lignes']:
                montant_ht += ligne['qte'] * ligne['pu']
            
            taux_tva = Decimal('18')
            montant_tva = montant_ht * taux_tva / 100
            montant_ttc = montant_ht + montant_tva
            
            facture = Facture.objects.create(
                entreprise=entreprise,
                numero=data['numero'],
                type_facture=data['type'],
                tiers=data['tiers'],
                date_facture=data['date_facture'],
                date_echeance=data['date_echeance'],
                montant_ht=montant_ht,
                montant_tva=montant_tva,
                montant_ttc=montant_ttc,
                montant_paye=Decimal('0'),
                statut=data['statut'],
            )
            
            # Créer les lignes
            for ligne in data['lignes']:
                montant_ligne_ht = ligne['qte'] * ligne['pu']
                montant_ligne_tva = montant_ligne_ht * taux_tva / 100
                LigneFacture.objects.create(
                    facture=facture,
                    designation=ligne['designation'],
                    quantite=ligne['qte'],
                    prix_unitaire=ligne['pu'],
                    taux_tva=taux_tva,
                    montant_ht=montant_ligne_ht,
                    montant_tva=montant_ligne_tva,
                    montant_ttc=montant_ligne_ht + montant_ligne_tva,
                    compte_comptable=ligne['compte'],
                )
            
            nb_factures += 1
        
        self.stdout.write(f'  {nb_factures} factures impayées créées')

    def creer_reglements(self, entreprise):
        """Créer des règlements de test"""
        
        if Reglement.objects.filter(entreprise=entreprise).exists():
            self.stdout.write('  Règlements déjà existants, ignoré')
            return
        
        today = timezone.now().date()
        
        # Récupérer les factures validées
        factures = Facture.objects.filter(entreprise=entreprise, statut='validee')
        
        if not factures.exists():
            self.stdout.write('  Aucune facture pour créer des règlements')
            return
        
        modes_paiement = ['virement', 'cheque', 'especes', 'mobile']
        reglements_data = []
        
        # Créer des règlements partiels et complets pour quelques factures
        for i, facture in enumerate(factures[:4], 1):
            # Règlement partiel (50%) pour les 2 premières factures
            if i <= 2:
                montant = facture.montant_ttc * Decimal('0.5')
                reference = f"REF-PART-{i:03d}"
            else:
                # Règlement complet pour les autres
                montant = facture.montant_ttc
                reference = f"REF-COMP-{i:03d}"
            
            reglements_data.append({
                'numero': f'REG-2026-{i:03d}',
                'facture': facture,
                'date': today - timedelta(days=10-i*2),
                'montant': montant,
                'mode': modes_paiement[i % len(modes_paiement)],
                'reference': reference,
            })
        
        nb_reglements = 0
        for data in reglements_data:
            reglement = Reglement.objects.create(
                entreprise=entreprise,
                numero=data['numero'],
                facture=data['facture'],
                date_reglement=data['date'],
                montant=data['montant'],
                mode_paiement=data['mode'],
                reference=data['reference'],
                notes=f"Règlement de la facture {data['facture'].numero}",
            )
            
            # Mettre à jour le montant payé de la facture
            data['facture'].montant_paye += data['montant']
            if data['facture'].montant_paye >= data['facture'].montant_ttc:
                data['facture'].statut = 'payee'
            data['facture'].save()
            
            nb_reglements += 1
        
        self.stdout.write(f'  {nb_reglements} règlements créés')
