from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from openpyxl import Workbook
from datetime import datetime

from .models import Employe, ContratEmploye
from .forms import EmployeForm, ContratForm
from core.views import log_activity


class EmployeListView(LoginRequiredMixin, ListView):
    """Liste des employés avec recherche et filtres"""
    model = Employe
    template_name = 'employes/list.html'
    context_object_name = 'employes'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Employe.objects.select_related(
            'etablissement', 'service', 'poste'
        ).all()
        
        # Recherche
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(prenoms__icontains=search) |
                Q(matricule__icontains=search) |
                Q(num_cnss_individuel__icontains=search)
            )
        
        # Filtres
        statut = self.request.GET.get('statut', '')
        if statut:
            queryset = queryset.filter(statut_employe=statut)
        
        type_contrat = self.request.GET.get('type_contrat', '')
        if type_contrat:
            queryset = queryset.filter(type_contrat=type_contrat)
        
        service = self.request.GET.get('service', '')
        if service:
            queryset = queryset.filter(service_id=service)
        
        sexe = self.request.GET.get('sexe', '')
        if sexe:
            queryset = queryset.filter(sexe=sexe)
        
        return queryset.order_by('-date_creation')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['statut_filter'] = self.request.GET.get('statut', '')
        context['type_contrat_filter'] = self.request.GET.get('type_contrat', '')
        context['service_filter'] = self.request.GET.get('service', '')
        context['sexe_filter'] = self.request.GET.get('sexe', '')
        
        # Statistiques rapides
        context['total_employes'] = self.get_queryset().count()
        context['employes_actifs'] = self.get_queryset().filter(statut_employe='Actif').count()
        
        # Services pour le filtre
        from core.models import Service
        context['services'] = Service.objects.filter(actif=True)
        
        return context


class EmployeDetailView(LoginRequiredMixin, DetailView):
    """Fiche détaillée d'un employé"""
    model = Employe
    template_name = 'employes/detail.html'
    context_object_name = 'employe'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employe = self.object
        
        # Contrats
        context['contrats'] = ContratEmploye.objects.filter(
            employe=employe
        ).order_by('-date_debut')
        
        # Âge et ancienneté
        if employe.date_naissance:
            today = datetime.now().date()
            age = (today - employe.date_naissance).days // 365
            context['age'] = age
        
        if employe.date_embauche:
            anciennete = (datetime.now().date() - employe.date_embauche).days // 365
            context['anciennete'] = anciennete
        
        # Salaire actuel (éléments de salaire)
        from paie.models import ElementSalaire
        try:
            # Récupérer le salaire de base
            element_base = ElementSalaire.objects.filter(
                employe=employe,
                rubrique__code_rubrique__icontains='SAL_BASE',
                actif=True
            ).first()
            context['salaire_base'] = element_base.montant if element_base else None
        except Exception:
            context['salaire_base'] = None
        
        # Solde de congés
        from temps_travail.models import SoldeConge
        try:
            context['solde_conges'] = SoldeConge.objects.get(
                employe=employe,
                annee=datetime.now().year
            )
        except SoldeConge.DoesNotExist:
            context['solde_conges'] = None
        
        # Documents
        from .models import DocumentEmploye
        context['documents'] = DocumentEmploye.objects.filter(
            employe=employe
        ).order_by('-date_ajout')
        
        # Statistiques documents par type
        from django.db.models import Count
        context['stats_documents'] = DocumentEmploye.objects.filter(
            employe=employe
        ).values('type_document').annotate(count=Count('id'))
        
        return context


class EmployeCreateView(LoginRequiredMixin, CreateView):
    """Création d'un nouvel employé"""
    model = Employe
    form_class = EmployeForm
    template_name = 'employes/form.html'
    success_url = reverse_lazy('employes:list')
    
    def form_valid(self, form):
        employe = form.save(commit=False)
        
        # Générer le matricule si vide
        if not employe.matricule:
            employe.matricule = self.generer_matricule()
        
        employe.utilisateur_creation = self.request.user
        employe.save()
        
        # Log
        log_activity(
            self.request,
            f"Création employé {employe.matricule}",
            'employes',
            'employes',
            employe.id
        )
        
        messages.success(
            self.request,
            f'Employé {employe.nom} {employe.prenoms} créé avec succès (Matricule: {employe.matricule})'
        )
        
        return super().form_valid(form)
    
    def generer_matricule(self):
        """Génère un matricule automatique"""
        annee = datetime.now().year
        dernier = Employe.objects.filter(
            matricule__startswith=f'EMP{annee}'
        ).order_by('-matricule').first()
        
        if dernier:
            numero = int(dernier.matricule[-4:]) + 1
        else:
            numero = 1
        
        return f'EMP{annee}{numero:04d}'


class EmployeUpdateView(LoginRequiredMixin, UpdateView):
    """Modification d'un employé"""
    model = Employe
    form_class = EmployeForm
    template_name = 'employes/form.html'
    
    def get_success_url(self):
        return reverse_lazy('employes:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        employe = form.save(commit=False)
        employe.utilisateur_modification = self.request.user
        employe.save()
        
        # Log
        log_activity(
            self.request,
            f"Modification employé {employe.matricule}",
            'employes',
            'employes',
            employe.id
        )
        
        messages.success(
            self.request,
            f'Employé {employe.nom} {employe.prenoms} modifié avec succès'
        )
        
        return super().form_valid(form)


class EmployeDeleteView(LoginRequiredMixin, DeleteView):
    """Suppression d'un employé"""
    model = Employe
    template_name = 'employes/delete.html'
    success_url = reverse_lazy('employes:list')
    
    def delete(self, request, *args, **kwargs):
        employe = self.get_object()
        
        # Log
        log_activity(
            request,
            f"Suppression employé {employe.matricule}",
            'employes',
            'employes',
            employe.id
        )
        
        messages.warning(
            request,
            f'Employé {employe.nom} {employe.prenoms} supprimé'
        )
        
        return super().delete(request, *args, **kwargs)


@login_required
def employe_export_excel(request):
    """Export de la liste des employés en Excel"""
    employes = Employe.objects.select_related(
        'etablissement', 'service', 'poste'
    ).filter(statut_employe='Actif')
    
    # Créer le workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Employés"
    
    # En-têtes
    headers = [
        'Matricule', 'Civilité', 'Nom', 'Prénoms', 'Sexe', 'Date naissance',
        'N° CNSS', 'Téléphone', 'Email', 'Établissement', 'Service', 'Poste',
        'Date embauche', 'Type contrat', 'Statut'
    ]
    ws.append(headers)
    
    # Données
    for emp in employes:
        ws.append([
            emp.matricule,
            emp.civilite,
            emp.nom,
            emp.prenoms,
            emp.sexe,
            emp.date_naissance.strftime('%d/%m/%Y') if emp.date_naissance else '',
            emp.num_cnss_individuel,
            emp.telephone_principal,
            emp.email_professionnel,
            emp.etablissement.nom_etablissement if emp.etablissement else '',
            emp.service.nom_service if emp.service else '',
            emp.poste.intitule_poste if emp.poste else '',
            emp.date_embauche.strftime('%d/%m/%Y') if emp.date_embauche else '',
            emp.type_contrat,
            emp.statut_employe
        ])
    
    # Réponse HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=employes_{datetime.now().strftime("%Y%m%d")}.xlsx'
    
    wb.save(response)
    
    # Log
    log_activity(
        request,
        "Export Excel employés",
        'employes'
    )
    
    return response


@login_required
def employe_contrat_create(request, employe_id):
    """Créer un nouveau contrat pour un employé"""
    employe = get_object_or_404(Employe, pk=employe_id)
    
    if request.method == 'POST':
        form = ContratForm(request.POST, request.FILES)
        if form.is_valid():
            contrat = form.save(commit=False)
            contrat.employe = employe
            contrat.save()
            
            # Mettre à jour les infos de l'employé
            employe.type_contrat = contrat.type_contrat
            employe.date_debut_contrat = contrat.date_debut
            employe.date_fin_contrat = contrat.date_fin
            employe.num_contrat = contrat.num_contrat
            employe.save()
            
            messages.success(request, 'Contrat créé avec succès')
            return redirect('employes:detail', pk=employe.id)
    else:
        form = ContratForm()
    
    return render(request, 'employes/contrat_form.html', {
        'form': form,
        'employe': employe
    })


@login_required
def employe_document_upload(request, employe_id):
    """Télécharger un document pour un employé"""
    from .models import DocumentEmploye
    
    employe = get_object_or_404(Employe, pk=employe_id)
    
    if request.method == 'POST':
        type_document = request.POST.get('type_document')
        titre = request.POST.get('titre')
        description = request.POST.get('description', '')
        date_document = request.POST.get('date_document')
        date_expiration = request.POST.get('date_expiration')
        confidentiel = request.POST.get('confidentiel') == 'on'
        fichier = request.FILES.get('fichier')
        
        if not all([type_document, titre, fichier]):
            messages.error(request, 'Veuillez remplir tous les champs obligatoires')
            return redirect('employes:detail', pk=employe.id)
        
        # Créer le document
        document = DocumentEmploye.objects.create(
            employe=employe,
            type_document=type_document,
            titre=titre,
            description=description,
            fichier=fichier,
            date_document=date_document if date_document else None,
            date_expiration=date_expiration if date_expiration else None,
            confidentiel=confidentiel,
            ajoute_par=request.user
        )
        
        # Log
        log_activity(
            request,
            f"Ajout document {titre} pour {employe.matricule}",
            'employes',
            'employes',
            employe.id
        )
        
        messages.success(request, f'Document "{titre}" ajouté avec succès')
        return redirect('employes:detail', pk=employe.id)
    
    return redirect('employes:detail', pk=employe.id)


@login_required
def employe_document_delete(request, document_id):
    """Supprimer un document d'employé"""
    from .models import DocumentEmploye
    
    document = get_object_or_404(DocumentEmploye, pk=document_id)
    employe = document.employe
    
    if request.method == 'POST':
        titre = document.titre
        document.delete()
        
        # Log
        log_activity(
            request,
            f"Suppression document {titre} pour {employe.matricule}",
            'employes',
            'employes',
            employe.id
        )
        
        messages.success(request, f'Document "{titre}" supprimé avec succès')
    
    return redirect('employes:detail', pk=employe.id)
