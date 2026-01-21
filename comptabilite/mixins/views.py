"""
Mixins réutilisables pour les vues comptables.

Fournissent des fonctionnalités communes:
- Permissions par entreprise
- Contrôle d'accès
- Pagination
- Filtrage
- Audit
"""

from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)


class EntrepriseRequiredMixin(LoginRequiredMixin):
    """Garantit que l'utilisateur appartient à une entreprise."""
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'entreprise') or not request.user.entreprise:
            raise PermissionDenied("Vous n'appartinez à aucune entreprise")
        return super().dispatch(request, *args, **kwargs)


class ComptabiliteAccessMixin(EntrepriseRequiredMixin, UserPassesTestMixin):
    """
    Mixin pour vérifier l'accès au module de comptabilité.
    
    L'utilisateur doit:
    - Être connecté
    - Appartenir à une entreprise
    - Avoir la permission 'comptabilite'
    """
    
    def test_func(self):
        """Vérifie si l'utilisateur a accès à la comptabilité."""
        user = self.request.user
        
        # Admin = accès complet
        if user.is_superuser or user.est_admin_entreprise:
            return True
        
        # Vérifie la permission
        return user.has_perm('comptabilite.view_comptabilite')
    
    def handle_no_permission(self):
        if self.request.is_ajax() or self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Permission refusée'}, status=403)
        raise PermissionDenied("Accès refusé au module de comptabilité")


class EntrepriseFilterMixin:
    """Filtre automatiquement les objets par entreprise."""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(entreprise=self.request.user.entreprise)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entreprise'] = self.request.user.entreprise
        return context


class AuditMixin:
    """Enregistre les actions en piste d'audit."""
    
    def get_audit_data(self):
        """Retourne les données pour l'audit."""
        return {}
    
    def form_valid(self, form):
        """Enregistre l'action en audit avant sauvegarde."""
        response = super().form_valid(form)
        
        from ..models import PisteAudit
        try:
            PisteAudit.objects.create(
                entreprise=self.request.user.entreprise,
                utilisateur=self.request.user,
                action=self.get_audit_action(),
                module=self.get_audit_module(),
                type_objet=self.model.__name__,
                id_objet=str(self.object.id),
                donnees_nouvelles=str(self.get_audit_data())
            )
        except Exception as e:
            logger.error(f"Erreur audit: {e}")
        
        return response
    
    def get_audit_action(self):
        """Retourne le type d'action ('create' ou 'update')."""
        return 'update' if self.object.pk else 'create'
    
    def get_audit_module(self):
        """Retourne le module pour l'audit."""
        return self.model._meta.verbose_name_plural


class PaginationMixin:
    """Ajoute la pagination standardisée."""
    
    paginate_by = 50
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['paginate_by'] = self.paginate_by
        return context


class SearchMixin:
    """Ajoute la recherche sur les listes."""
    
    search_fields = []
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        search = self.request.GET.get('search', '').strip()
        if search and self.search_fields:
            from django.db.models import Q
            q = Q()
            for field in self.search_fields:
                q |= Q(**{f"{field}__icontains": search})
            queryset = queryset.filter(q)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class FilterMixin:
    """Ajoute les filtres standardisés."""
    
    filter_fields = []
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        for field in self.filter_fields:
            value = self.request.GET.get(field)
            if value:
                queryset = queryset.filter(**{field: value})
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for field in self.filter_fields:
            context[f'{field}_value'] = self.request.GET.get(field, '')
        return context


class ExportMixin:
    """Ajoute l'export des données."""
    
    def get_export_filename(self):
        """Retourne le nom du fichier d'export."""
        return f"export_{self.model._meta.model_name}"
    
    def export_csv(self, queryset):
        """Exporte en CSV."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{self.get_export_filename()}.csv"'
        
        writer = csv.writer(response)
        # À implémenter par subclass
        return response
    
    def export_excel(self, queryset):
        """Exporte en Excel."""
        # À implémenter avec openpyxl si nécessaire
        pass
