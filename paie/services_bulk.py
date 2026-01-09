"""
Service de calcul de paie en masse avec optimisations.
Permet le calcul parallélisé et batch des bulletins.
"""
from decimal import Decimal
from datetime import date
from django.db import transaction
from django.db.models import Prefetch
from typing import List, Dict, Tuple, Optional
import logging

from .models import (
    BulletinPaie, LigneBulletin, ElementSalaire, CumulPaie,
    RubriquePaie, PeriodePaie
)
from .cache_service import PayrollCacheService
from .services import MoteurCalculPaie
from employes.models import Employe

logger = logging.getLogger(__name__)


class BulkPayrollService:
    """
    Service optimisé pour le calcul de paie en masse.
    Réduit drastiquement le nombre de requêtes DB.
    """
    
    def __init__(self, periode: PeriodePaie, entreprise):
        self.periode = periode
        self.entreprise = entreprise
        self.errors = []
        self.bulletins_created = 0
        
        # Préchauffer le cache
        PayrollCacheService.warmup_cache(periode.annee)
    
    def calculer_tous_bulletins(self, utilisateur) -> Dict:
        """
        Calcule tous les bulletins pour la période.
        
        Returns:
            Dict avec statistiques: bulletins_crees, erreurs, temps_execution
        """
        import time
        start_time = time.time()
        
        # Récupérer tous les employés actifs avec prefetch optimisé
        employes = self._get_employes_optimized()
        
        self.errors = []
        self.bulletins_created = 0
        
        with transaction.atomic():
            # Supprimer les bulletins existants en une seule requête
            deleted_count = BulletinPaie.objects.filter(
                periode=self.periode,
                employe__entreprise=self.entreprise,
            ).delete()[0]
            
            if deleted_count:
                logger.info(f"Supprimé {deleted_count} bulletins existants")
            
            # Calculer par batch pour éviter la surcharge mémoire
            batch_size = 50
            for i in range(0, len(employes), batch_size):
                batch = employes[i:i + batch_size]
                self._process_batch(batch, utilisateur)
        
        elapsed = time.time() - start_time
        
        return {
            'bulletins_crees': self.bulletins_created,
            'erreurs': self.errors,
            'temps_execution': round(elapsed, 2),
            'employes_total': len(employes),
        }
    
    def _get_employes_optimized(self) -> List[Employe]:
        """
        Récupère les employés avec toutes les relations préchargées.
        """
        return list(
            Employe.objects.filter(
                entreprise=self.entreprise,
                statut_employe='actif'
            ).select_related(
                'etablissement',
                'service',
                'poste',
                'devise_paie',
            ).prefetch_related(
                Prefetch(
                    'elements_salaire',
                    queryset=ElementSalaire.objects.filter(
                        actif=True,
                    ).select_related('rubrique').order_by('rubrique__ordre_calcul')
                )
            ).only(
                'id', 'matricule', 'nom', 'prenoms', 'sexe',
                'date_embauche', 'date_naissance', 'type_contrat',
                'date_debut_contrat', 'situation_matrimoniale',
                'nombre_enfants', 'mode_paiement',
                'etablissement_id', 'service_id', 'poste_id',
                'devise_paie_id', 'entreprise_id', 'statut_employe',
            )
        )
    
    def _process_batch(self, employes: List[Employe], utilisateur):
        """
        Traite un batch d'employés.
        """
        for employe in employes:
            try:
                moteur = MoteurCalculPaie(employe, self.periode)
                bulletin = moteur.generer_bulletin(utilisateur=utilisateur)
                self.bulletins_created += 1
            except Exception as e:
                error_msg = f"{employe.matricule}: {str(e)}"
                self.errors.append(error_msg)
                logger.error(f"Erreur calcul bulletin: {error_msg}")
    
    @classmethod
    def recalculer_bulletin(cls, bulletin_id: int, utilisateur) -> Tuple[bool, str]:
        """
        Recalcule un bulletin spécifique.
        
        Returns:
            Tuple (success, message)
        """
        try:
            bulletin = BulletinPaie.objects.select_related(
                'employe', 'periode'
            ).get(pk=bulletin_id)
            
            if bulletin.statut_bulletin == 'valide':
                return False, "Bulletin déjà validé, impossible de recalculer"
            
            employe = bulletin.employe
            periode = bulletin.periode
            
            # Supprimer l'ancien bulletin
            bulletin.delete()
            
            # Recalculer
            moteur = MoteurCalculPaie(employe, periode)
            nouveau_bulletin = moteur.generer_bulletin(utilisateur=utilisateur)
            
            return True, f"Bulletin {nouveau_bulletin.numero_bulletin} recalculé"
            
        except BulletinPaie.DoesNotExist:
            return False, "Bulletin non trouvé"
        except Exception as e:
            return False, f"Erreur: {str(e)}"


class PayrollStatsService:
    """
    Service pour les statistiques de paie optimisées.
    """
    
    @staticmethod
    def get_stats_periode(periode: PeriodePaie, entreprise) -> Dict:
        """
        Calcule les statistiques d'une période en une seule requête.
        """
        from django.db.models import Sum, Count, Avg, Min, Max
        
        stats = BulletinPaie.objects.filter(
            periode=periode,
            employe__entreprise=entreprise,
        ).aggregate(
            total_brut=Sum('salaire_brut'),
            total_net=Sum('net_a_payer'),
            total_cnss_employe=Sum('cnss_employe'),
            total_cnss_employeur=Sum('cnss_employeur'),
            total_irg=Sum('irg'),
            total_vf=Sum('versement_forfaitaire'),
            total_ta=Sum('taxe_apprentissage'),
            count=Count('id'),
            avg_brut=Avg('salaire_brut'),
            avg_net=Avg('net_a_payer'),
            min_net=Min('net_a_payer'),
            max_net=Max('net_a_payer'),
        )
        
        # Convertir None en 0
        for key in stats:
            if stats[key] is None:
                stats[key] = Decimal('0') if 'total' in key or 'avg' in key or 'min' in key or 'max' in key else 0
        
        # Calculer les charges patronales totales
        stats['total_charges_patronales'] = (
            stats['total_cnss_employeur'] + 
            stats['total_vf'] + 
            stats['total_ta']
        )
        
        # Coût total employeur
        stats['cout_total_employeur'] = stats['total_brut'] + stats['total_charges_patronales']
        
        return stats
    
    @staticmethod
    def get_stats_annuelles(annee: int, entreprise) -> Dict:
        """
        Statistiques annuelles cumulées.
        """
        from django.db.models import Sum, Count
        
        return BulletinPaie.objects.filter(
            annee_paie=annee,
            employe__entreprise=entreprise,
            statut_bulletin__in=['calcule', 'valide'],
        ).aggregate(
            total_brut=Sum('salaire_brut'),
            total_net=Sum('net_a_payer'),
            total_cnss_employe=Sum('cnss_employe'),
            total_cnss_employeur=Sum('cnss_employeur'),
            total_irg=Sum('irg'),
            count=Count('id'),
        )
