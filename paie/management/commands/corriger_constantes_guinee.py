"""
Correction des constantes de paie selon la législation guinéenne.

Ce script corrige les valeurs incorrectes et ajoute les constantes manquantes :
- Heures Supplémentaires (Code du Travail Art. 221)
- Taxe d'Apprentissage : 2%
- Congés payés (1,5j/mois au lieu de 2,5j/mois)
- Contribution ONFPP (1,5%)

Usage:
    python manage.py corriger_constantes_guinee
"""
from decimal import Decimal
from datetime import date
from django.core.management.base import BaseCommand
from paie.models import Constante


class Command(BaseCommand):
    help = 'Corrige les constantes de paie selon la législation guinéenne (CGI 2022 + Code du Travail Art. 221)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('=' * 70))
        self.stdout.write(self.style.NOTICE('CORRECTION DES CONSTANTES DE PAIE - LÉGISLATION GUINÉENNE'))
        self.stdout.write(self.style.NOTICE('=' * 70))
        
        # Date de début de validité pour les nouvelles constantes
        date_validite = date(2022, 1, 1)  # CGI 2022
        
        # ============================================
        # 1. CORRECTIONS DES HEURES SUPPLÉMENTAIRES
        # ============================================
        self.stdout.write('\n📊 1. HEURES SUPPLÉMENTAIRES (Code du Travail Art. 221)')
        self.stdout.write('-' * 50)
        
        corrections_hs = [
            {
                'code': 'TAUX_HS_4PREM',
                'libelle': 'Taux 4 premières HS/semaine',
                'valeur': Decimal('130.00'),
                'type_valeur': 'pourcentage',
                'categorie': 'temps',
                'unite': '%',
                'description': 'Majoration 4 premières heures supplémentaires/semaine: +30% (Art. 221)'
            },
            {
                'code': 'TAUX_HS_AUDELA',
                'libelle': 'Taux au-delà 4 HS/semaine',
                'valeur': Decimal('160.00'),
                'type_valeur': 'pourcentage',
                'categorie': 'temps',
                'unite': '%',
                'description': 'Majoration au-delà de 4 heures supplémentaires/semaine: +60% (Art. 221)'
            },
            {
                'code': 'TAUX_HS_NUIT',
                'libelle': 'Taux HS heures de nuit',
                'valeur': Decimal('120.00'),
                'type_valeur': 'pourcentage',
                'categorie': 'temps',
                'unite': '%',
                'description': 'Majoration heures de nuit (20h-6h): +20% (Art. 221 Code du Travail)'
            },
            {
                'code': 'TAUX_HS_FERIE_JOUR',
                'libelle': 'Taux jour férié (jour)',
                'valeur': Decimal('160.00'),
                'type_valeur': 'pourcentage',
                'categorie': 'temps',
                'unite': '%',
                'description': 'Majoration jour férié (journée): +60% (Art. 221)'
            },
            {
                'code': 'TAUX_HS_FERIE_NUIT',
                'libelle': 'Taux jour férié (nuit)',
                'valeur': Decimal('200.00'),
                'type_valeur': 'pourcentage',
                'categorie': 'temps',
                'unite': '%',
                'description': 'Majoration jour férié (nuit): +100% (Art. 221)'
            },
        ]
        
        # Supprimer les anciennes constantes HS incorrectes
        anciennes_hs = ['TAUX_HS_JOUR_15', 'TAUX_HS_JOUR_25', 'TAUX_HS_FERIE']
        for code in anciennes_hs:
            deleted, _ = Constante.objects.filter(code=code).delete()
            if deleted:
                self.stdout.write(self.style.WARNING(f'  🗑️  Supprimé: {code} (ancien format)'))
        
        for data in corrections_hs:
            obj, created = Constante.objects.update_or_create(
                code=data['code'],
                defaults={
                    'libelle': data['libelle'],
                    'valeur': data['valeur'],
                    'type_valeur': data['type_valeur'],
                    'categorie': data['categorie'],
                    'unite': data['unite'],
                    'description': data['description'],
                    'date_debut_validite': date_validite,
                    'actif': True,
                }
            )
            status = '✅ Créé' if created else '🔄 Mis à jour'
            self.stdout.write(self.style.SUCCESS(f'  {status}: {data["code"]} = {data["valeur"]}%'))
        
        # ============================================
        # 2. CORRECTION TAXE D'APPRENTISSAGE
        # ============================================
        self.stdout.write('\n📊 2. TAXE D\'APPRENTISSAGE (CGI 2022)')
        self.stdout.write('-' * 50)
        
        obj, created = Constante.objects.update_or_create(
            code='TAUX_TA',
            defaults={
                'libelle': 'Taxe d\'Apprentissage',
                'valeur': Decimal('2.00'),
                'type_valeur': 'pourcentage',
                'categorie': 'general',
                'unite': '%',
                'description': 'Taxe d\'apprentissage à charge de l\'employeur (2% de la masse salariale)',
                'date_debut_validite': date_validite,
                'actif': True,
            }
        )
        status = '✅ Créé' if created else '🔄 Mis à jour'
        self.stdout.write(self.style.SUCCESS(f'  {status}: TAUX_TA = 2%'))
        
        # ============================================
        # 3. CONTRIBUTION ONFPP
        # ============================================
        self.stdout.write('\n📊 3. CONTRIBUTION ONFPP')
        self.stdout.write('-' * 50)
        
        obj, created = Constante.objects.update_or_create(
            code='TAUX_ONFPP',
            defaults={
                'libelle': 'Contribution ONFPP',
                'valeur': Decimal('1.50'),
                'type_valeur': 'pourcentage',
                'categorie': 'general',
                'unite': '%',
                'description': 'Contribution ONFPP: 1,5% (0,5% apprentissage + 1% perfectionnement)',
                'date_debut_validite': date_validite,
                'actif': True,
            }
        )
        status = '✅ Créé' if created else '🔄 Mis à jour'
        self.stdout.write(self.style.SUCCESS(f'  {status}: TAUX_ONFPP = 1.5%'))
        
        # ============================================
        # 4. CONSTANTES CONGÉS PAYÉS
        # ============================================
        self.stdout.write('\n📊 4. CONGÉS PAYÉS (Code du Travail)')
        self.stdout.write('-' * 50)
        
        conges_constantes = [
            {
                'code': 'CONGES_JOURS_MOIS',
                'libelle': 'Jours de congés par mois',
                'valeur': Decimal('1.50'),
                'type_valeur': 'nombre',
                'categorie': 'temps',
                'unite': 'jours',
                'description': 'Acquisition congés: 1,5 jour ouvrable par mois (18j/an)'
            },
            {
                'code': 'CONGES_JOURS_ANNUELS',
                'libelle': 'Jours de congés annuels',
                'valeur': Decimal('18.00'),
                'type_valeur': 'nombre',
                'categorie': 'temps',
                'unite': 'jours',
                'description': 'Congés annuels de base: 18 jours ouvrables'
            },
            {
                'code': 'CONGES_MOINS_18ANS_MOIS',
                'libelle': 'Jours de congés moins de 18 ans',
                'valeur': Decimal('2.00'),
                'type_valeur': 'nombre',
                'categorie': 'temps',
                'unite': 'jours',
                'description': 'Acquisition congés pour moins de 18 ans: 2 jours/mois (24j/an)'
            },
            {
                'code': 'CONGES_ANCIENNETE_5ANS',
                'libelle': 'Majoration congés ancienneté',
                'valeur': Decimal('2.00'),
                'type_valeur': 'nombre',
                'categorie': 'temps',
                'unite': 'jours',
                'description': 'Majoration congés: +2 jours par tranche de 5 ans d\'ancienneté'
            },
        ]
        
        for data in conges_constantes:
            obj, created = Constante.objects.update_or_create(
                code=data['code'],
                defaults={
                    'libelle': data['libelle'],
                    'valeur': data['valeur'],
                    'type_valeur': data['type_valeur'],
                    'categorie': data['categorie'],
                    'unite': data['unite'],
                    'description': data['description'],
                    'date_debut_validite': date_validite,
                    'actif': True,
                }
            )
            status = '✅ Créé' if created else '🔄 Mis à jour'
            self.stdout.write(self.style.SUCCESS(f'  {status}: {data["code"]} = {data["valeur"]}'))
        
        # ============================================
        # 5. CONSTANTES TEMPS DE TRAVAIL
        # ============================================
        self.stdout.write('\n📊 5. TEMPS DE TRAVAIL')
        self.stdout.write('-' * 50)
        
        temps_constantes = [
            {
                'code': 'DUREE_HEBDO_LEGALE',
                'libelle': 'Durée hebdomadaire légale',
                'valeur': Decimal('40.00'),
                'type_valeur': 'nombre',
                'categorie': 'temps',
                'unite': 'heures',
                'description': 'Durée légale du travail: 40 heures/semaine'
            },
            {
                'code': 'LIMITE_HS_ANNUELLE',
                'libelle': 'Limite HS sans autorisation',
                'valeur': Decimal('100.00'),
                'type_valeur': 'nombre',
                'categorie': 'temps',
                'unite': 'heures',
                'description': 'Limite heures supplémentaires/an sans autorisation'
            },
        ]
        
        for data in temps_constantes:
            obj, created = Constante.objects.update_or_create(
                code=data['code'],
                defaults={
                    'libelle': data['libelle'],
                    'valeur': data['valeur'],
                    'type_valeur': data['type_valeur'],
                    'categorie': data['categorie'],
                    'unite': data['unite'],
                    'description': data['description'],
                    'date_debut_validite': date_validite,
                    'actif': True,
                }
            )
            status = '✅ Créé' if created else '🔄 Mis à jour'
            self.stdout.write(self.style.SUCCESS(f'  {status}: {data["code"]} = {data["valeur"]}'))
        
        # ============================================
        # RÉCAPITULATIF
        # ============================================
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('✅ CORRECTION DES CONSTANTES TERMINÉE'))
        self.stdout.write('=' * 70)
        
        self.stdout.write('\n📋 RÉCAPITULATIF DES VALEURS LÉGALES:')
        self.stdout.write('-' * 50)
        self.stdout.write('  Heures Supplémentaires (Art. 221):')
        self.stdout.write('    • 4 premières HS/semaine: +30% (130%)')
        self.stdout.write('    • Au-delà 4 HS/semaine: +60% (160%)')
        self.stdout.write('    • Heures de nuit (20h-6h): +20% (120%)')
        self.stdout.write('    • Jour férié (jour): +60% (160%)')
        self.stdout.write('    • Jour férié (nuit): +100% (200%)')
        self.stdout.write('')
        self.stdout.write('  Charges Patronales:')
        self.stdout.write('    • CNSS Employeur: 18%')
        self.stdout.write('    • Versement Forfaitaire (VF): 6%')
        self.stdout.write('    • Taxe d\'Apprentissage (TA): 2%')
        self.stdout.write('    • Contribution ONFPP: 1,5%')
        self.stdout.write('')
        self.stdout.write('  Congés Payés:')
        self.stdout.write('    • Base: 1,5 jour/mois (18 jours/an)')
        self.stdout.write('    • Moins de 18 ans: 2 jours/mois (24 jours/an)')
        self.stdout.write('    • Ancienneté: +2 jours par tranche de 5 ans')
        self.stdout.write('')
