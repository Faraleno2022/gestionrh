"""
Correction du barème RTS selon le CGI 2022.

Le barème RTS pour les SALAIRES n'a que 5 tranches (pas de tranche 8%).
La tranche 8% concerne les revenus de capitaux mobiliers, PAS les salaires.

Barème correct:
- 0 - 1 000 000 GNF : 0%
- 1 000 001 - 5 000 000 GNF : 5%
- 5 000 001 - 10 000 000 GNF : 10%
- 10 000 001 - 20 000 000 GNF : 15%
- Au-delà de 20 000 000 GNF : 20%

Usage:
    python manage.py corriger_bareme_rts
"""
from decimal import Decimal
from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction
from paie.models import TrancheIRG


class Command(BaseCommand):
    help = 'Corrige le barème RTS (5 tranches sans la tranche 8% qui est pour les capitaux mobiliers)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('=' * 70))
        self.stdout.write(self.style.NOTICE('CORRECTION DU BARÈME RTS - CGI 2022'))
        self.stdout.write(self.style.NOTICE('=' * 70))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('⚠️  NOTE: La tranche 8% concerne les revenus de capitaux'))
        self.stdout.write(self.style.WARNING('    mobiliers (dividendes, intérêts), PAS les salaires.'))
        self.stdout.write('')
        
        # Barème RTS correct pour les salaires (5 tranches)
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
                'borne_superieure': Decimal('5000000'),
                'taux_irg': Decimal('5.00'),
            },
            {
                'numero_tranche': 3,
                'borne_inferieure': Decimal('5000001'),
                'borne_superieure': Decimal('10000000'),
                'taux_irg': Decimal('10.00'),
            },
            {
                'numero_tranche': 4,
                'borne_inferieure': Decimal('10000001'),
                'borne_superieure': Decimal('20000000'),
                'taux_irg': Decimal('15.00'),
            },
            {
                'numero_tranche': 5,
                'borne_inferieure': Decimal('20000001'),
                'borne_superieure': None,  # Illimité
                'taux_irg': Decimal('20.00'),
            },
        ]
        
        annee = date.today().year
        
        with transaction.atomic():
            # Supprimer toutes les anciennes tranches pour cette année
            deleted_count, _ = TrancheIRG.objects.filter(annee_validite=annee).delete()
            if deleted_count:
                self.stdout.write(f'🗑️  Supprimé {deleted_count} anciennes tranches pour {annee}')
            
            self.stdout.write('\n📊 BARÈME RTS CORRECT (5 tranches):')
            self.stdout.write('-' * 50)
            
            for tranche_data in tranches:
                tranche = TrancheIRG.objects.create(
                    annee_validite=annee,
                    numero_tranche=tranche_data['numero_tranche'],
                    borne_inferieure=tranche_data['borne_inferieure'],
                    borne_superieure=tranche_data['borne_superieure'],
                    taux_irg=tranche_data['taux_irg'],
                    date_debut_validite=date(annee, 1, 1),
                    actif=True
                )
                
                borne_sup = f"{tranche_data['borne_superieure']:>12,.0f}" if tranche_data['borne_superieure'] else "        ∞   "
                self.stdout.write(
                    f"  ✅ Tranche {tranche_data['numero_tranche']}: "
                    f"{tranche_data['borne_inferieure']:>12,.0f} - {borne_sup} GNF → "
                    f"{tranche_data['taux_irg']:>5}%"
                )
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('✅ BARÈME RTS CORRIGÉ AVEC SUCCÈS'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        # Afficher un exemple de calcul
        self.stdout.write('\n📋 EXEMPLE DE CALCUL (Base imposable: 7 875 000 GNF):')
        self.stdout.write('-' * 50)
        self.stdout.write('  Tranche 1: 1 000 000 × 0%  =         0 GNF')
        self.stdout.write('  Tranche 2: 4 000 000 × 5%  =   200 000 GNF')
        self.stdout.write('  Tranche 3: 2 875 000 × 10% =   287 500 GNF')
        self.stdout.write('  ' + '-' * 40)
        self.stdout.write('  TOTAL RTS                  =   487 500 GNF')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('  (Ancien calcul avec tranche 8%: 547 500 GNF)'))
        self.stdout.write(self.style.SUCCESS('  Économie pour l\'employé: 60 000 GNF/mois'))
