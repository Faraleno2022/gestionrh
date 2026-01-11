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

from .models import Employe, ContratEmploye, EvaluationEmploye, SanctionDisciplinaire, EnfantEmploye, ConjointEmploye
from .forms import EmployeForm, ContratForm, EvaluationEmployeForm, SanctionDisciplinaireForm
from core.views import log_activity


class EntrepriseEmployeQuerysetMixin(LoginRequiredMixin):
    def get_queryset(self):
        return Employe.objects.select_related(
            'etablissement', 'service', 'poste'
        ).filter(entreprise=self.request.user.entreprise)


class EmployeListView(LoginRequiredMixin, ListView):
    """Liste des employés avec recherche et filtres"""
    model = Employe
    template_name = 'employes/list.html'
    context_object_name = 'employes'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Employe.objects.select_related(
            'etablissement', 'service', 'poste'
        ).filter(entreprise=self.request.user.entreprise)
        
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
        context['employes_actifs'] = self.get_queryset().filter(statut_employe='actif').count()
        
        # Services pour le filtre
        from core.models import Service
        context['services'] = Service.objects.filter(
            actif=True,
            etablissement__societe__entreprise=self.request.user.entreprise,
        )
        
        return context


class EmployeDetailView(EntrepriseEmployeQuerysetMixin, DetailView):
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
        context['age'] = None
        context['anciennete'] = None
        
        if employe.date_naissance:
            today = datetime.now().date()
            context['age'] = (today - employe.date_naissance).days // 365
        
        if employe.date_embauche:
            context['anciennete'] = (datetime.now().date() - employe.date_embauche).days // 365
        
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

        context['evaluations_count'] = EvaluationEmploye.objects.filter(employe=employe).count()
        context['sanctions_count'] = SanctionDisciplinaire.objects.filter(employe=employe).count()

        context['last_evaluation'] = EvaluationEmploye.objects.filter(employe=employe).order_by('-date_evaluation').select_related('evaluateur').first()
        context['last_sanction'] = SanctionDisciplinaire.objects.filter(employe=employe).order_by('-date_notification', '-date_faits').first()
        
        # Statistiques documents par type
        from django.db.models import Count
        context['stats_documents'] = DocumentEmploye.objects.filter(
            employe=employe
        ).values('type_document').annotate(count=Count('id'))
        
        # Famille (conjoint et enfants)
        context['enfants'] = employe.enfants.all().order_by('-date_naissance')
        try:
            context['conjoint'] = employe.conjoint
        except ConjointEmploye.DoesNotExist:
            context['conjoint'] = None
        
        return context


class EmployeCreateView(LoginRequiredMixin, CreateView):
    """Création d'un nouvel employé"""
    model = Employe
    form_class = EmployeForm
    template_name = 'employes/form.html'
    success_url = reverse_lazy('employes:list')
    
    def form_valid(self, form):
        employe = form.save(commit=False)
        employe.entreprise = self.request.user.entreprise
        
        # Générer le matricule si vide
        if not employe.matricule:
            employe.matricule = self.generer_matricule()
        
        # S'assurer que nombre_enfants a une valeur par défaut
        if employe.nombre_enfants is None:
            employe.nombre_enfants = 0
        
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
            entreprise=self.request.user.entreprise,
            matricule__startswith=f'EMP{annee}'
        ).order_by('-matricule').first()
        
        if dernier:
            numero = int(dernier.matricule[-4:]) + 1
        else:
            numero = 1
        
        return f'EMP{annee}{numero:04d}'


class EmployeUpdateView(EntrepriseEmployeQuerysetMixin, UpdateView):
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


class EmployeDeleteView(EntrepriseEmployeQuerysetMixin, DeleteView):
    """Suppression d'un employé"""
    model = Employe
    template_name = 'employes/delete.html'
    success_url = reverse_lazy('employes:list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employe = self.get_object()
        
        # Compter les données liées qui seront supprimées
        donnees_liees = {
            'contrats': employe.contrats.count(),
            'documents': employe.documents.count(),
            'formations': employe.formations.count(),
            'evaluations': employe.evaluations.count(),
            'carrieres': employe.carrieres.count(),
            'sanctions': employe.sanctions.count(),
            'visites_medicales': employe.visites_medicales.count(),
            'accidents_travail': employe.accidents_travail.count(),
            'equipements_protection': employe.equipements_protection.count(),
        }
        
        # Données des autres modules
        try:
            donnees_liees['bulletins_paie'] = employe.bulletins.count()
            donnees_liees['elements_salaire'] = employe.elements_salaire.count()
            donnees_liees['cumuls_paie'] = employe.cumuls_paie.count()
            donnees_liees['avances_salaire'] = employe.avances_salaire.count()
            donnees_liees['saisies_arret'] = employe.saisies_arret.count()
        except:
            pass
        
        try:
            donnees_liees['conges'] = employe.conges.count()
            donnees_liees['pointages'] = employe.pointages.count()
            donnees_liees['absences'] = employe.absences.count()
            donnees_liees['arrets_travail'] = employe.arrets_travail.count()
            donnees_liees['soldes_conges'] = employe.soldes_conges.count()
        except:
            pass
        
        context['donnees_liees'] = donnees_liees
        context['total_donnees'] = sum(donnees_liees.values())
        
        return context
    
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
            f'Employé {employe.nom} {employe.prenoms} et toutes ses données associées ont été supprimés'
        )
        
        return super().delete(request, *args, **kwargs)


@login_required
def employe_export_excel(request):
    """Export de la liste des employés en Excel"""
    employes = Employe.objects.select_related(
        'etablissement', 'service', 'poste'
    ).filter(
        entreprise=request.user.entreprise,
        statut_employe='actif'
    )
    
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
    employe = get_object_or_404(Employe, pk=employe_id, entreprise=request.user.entreprise)
    
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
def evaluation_list(request, employe_id):
    employe = get_object_or_404(Employe, pk=employe_id, entreprise=request.user.entreprise)
    evaluations = EvaluationEmploye.objects.filter(employe=employe).select_related('evaluateur')
    return render(request, 'employes/evaluations/liste.html', {
        'employe': employe,
        'evaluations': evaluations,
    })


@login_required
def evaluation_create(request, employe_id):
    employe = get_object_or_404(Employe, pk=employe_id, entreprise=request.user.entreprise)

    if request.method == 'POST':
        form = EvaluationEmployeForm(request.POST, entreprise=request.user.entreprise)
        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.employe = employe
            evaluation.save()

            log_activity(
                request,
                f"Création évaluation {evaluation.annee_evaluation} - {employe.matricule}",
                'employes',
                'evaluations_employes',
                evaluation.id,
            )

            messages.success(request, 'Évaluation enregistrée avec succès')
            return redirect('employes:evaluation_detail', pk=evaluation.pk)
    else:
        form = EvaluationEmployeForm(entreprise=request.user.entreprise)

    return render(request, 'employes/evaluations/form.html', {
        'form': form,
        'employe': employe,
    })


@login_required
def evaluation_detail(request, pk):
    evaluation = get_object_or_404(EvaluationEmploye, pk=pk, employe__entreprise=request.user.entreprise)
    return render(request, 'employes/evaluations/detail.html', {
        'evaluation': evaluation,
        'employe': evaluation.employe,
    })


@login_required
def evaluation_delete(request, pk):
    evaluation = get_object_or_404(EvaluationEmploye, pk=pk, employe__entreprise=request.user.entreprise)
    employe = evaluation.employe

    if request.method == 'POST':
        evaluation_id = evaluation.id
        evaluation.delete()

        log_activity(
            request,
            f"Suppression évaluation {evaluation_id} - {employe.matricule}",
            'employes',
            'evaluations_employes',
            evaluation_id,
        )

        messages.success(request, 'Évaluation supprimée avec succès')
        return redirect('employes:evaluation_list', employe_id=employe.id)

    return render(request, 'employes/evaluations/delete.html', {
        'evaluation': evaluation,
        'employe': employe,
    })


@login_required
def sanction_list(request, employe_id):
    employe = get_object_or_404(Employe, pk=employe_id, entreprise=request.user.entreprise)
    sanctions = SanctionDisciplinaire.objects.filter(employe=employe)
    return render(request, 'employes/sanctions/liste.html', {
        'employe': employe,
        'sanctions': sanctions,
    })


@login_required
def sanction_create(request, employe_id):
    employe = get_object_or_404(Employe, pk=employe_id, entreprise=request.user.entreprise)

    if request.method == 'POST':
        form = SanctionDisciplinaireForm(request.POST, request.FILES)
        if form.is_valid():
            sanction = form.save(commit=False)
            sanction.employe = employe
            sanction.save()

            log_activity(
                request,
                f"Création sanction {sanction.get_type_sanction_display()} - {employe.matricule}",
                'employes',
                'sanctions_disciplinaires',
                sanction.id,
            )

            messages.success(request, 'Sanction enregistrée avec succès')
            return redirect('employes:sanction_detail', pk=sanction.pk)
    else:
        form = SanctionDisciplinaireForm()

    return render(request, 'employes/sanctions/form.html', {
        'form': form,
        'employe': employe,
    })


@login_required
def sanction_detail(request, pk):
    sanction = get_object_or_404(SanctionDisciplinaire, pk=pk, employe__entreprise=request.user.entreprise)
    return render(request, 'employes/sanctions/detail.html', {
        'sanction': sanction,
        'employe': sanction.employe,
    })


@login_required
def sanction_delete(request, pk):
    sanction = get_object_or_404(SanctionDisciplinaire, pk=pk, employe__entreprise=request.user.entreprise)
    employe = sanction.employe

    if request.method == 'POST':
        sanction_id = sanction.id
        sanction.delete()

        log_activity(
            request,
            f"Suppression sanction {sanction_id} - {employe.matricule}",
            'employes',
            'sanctions_disciplinaires',
            sanction_id,
        )

        messages.success(request, 'Sanction supprimée avec succès')
        return redirect('employes:sanction_list', employe_id=employe.id)

    return render(request, 'employes/sanctions/delete.html', {
        'sanction': sanction,
        'employe': employe,
    })


@login_required
def employe_document_upload(request, employe_id):
    """Télécharger un document pour un employé"""
    from .models import DocumentEmploye
    
    employe = get_object_or_404(Employe, pk=employe_id, entreprise=request.user.entreprise)
    
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
    
    document = get_object_or_404(DocumentEmploye, pk=document_id, employe__entreprise=request.user.entreprise)
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


@login_required
def sauvegarder_conjoint(request, employe_id):
    """Ajouter ou modifier le conjoint d'un employé"""
    employe = get_object_or_404(Employe, pk=employe_id, entreprise=request.user.entreprise)
    
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        prenoms = request.POST.get('prenoms', '').strip()
        
        if not nom or not prenoms:
            messages.error(request, 'Le nom et les prénoms du conjoint sont obligatoires')
            return redirect('employes:detail', pk=employe.id)
        
        # Récupérer ou créer le conjoint
        try:
            conjoint = employe.conjoint
        except ConjointEmploye.DoesNotExist:
            conjoint = ConjointEmploye(employe=employe)
        
        conjoint.nom = nom
        conjoint.prenoms = prenoms
        conjoint.date_naissance = request.POST.get('date_naissance') or None
        conjoint.sexe = request.POST.get('sexe') or None
        conjoint.telephone = request.POST.get('telephone', '')
        conjoint.profession = request.POST.get('profession', '')
        conjoint.employeur = request.POST.get('employeur', '')
        conjoint.date_mariage = request.POST.get('date_mariage') or None
        conjoint.lieu_mariage = request.POST.get('lieu_mariage', '')
        
        if 'acte_mariage' in request.FILES:
            conjoint.acte_mariage = request.FILES['acte_mariage']
        
        conjoint.save()
        
        # Mettre à jour le nombre d'enfants et la situation matrimoniale
        if employe.situation_matrimoniale != 'marie':
            employe.situation_matrimoniale = 'marie'
            employe.save(update_fields=['situation_matrimoniale'])
        
        log_activity(
            request,
            f"Modification conjoint pour {employe.matricule}",
            'employes',
            'employes',
            employe.id
        )
        
        messages.success(request, f'Conjoint {conjoint.nom} {conjoint.prenoms} enregistré avec succès')
    
    return redirect('employes:detail', pk=employe.id)


@login_required
def sauvegarder_enfant(request, employe_id):
    """Ajouter ou modifier un enfant d'un employé"""
    employe = get_object_or_404(Employe, pk=employe_id, entreprise=request.user.entreprise)
    
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        prenoms = request.POST.get('prenoms', '').strip()
        date_naissance = request.POST.get('date_naissance')
        
        if not nom or not prenoms or not date_naissance:
            messages.error(request, 'Le nom, les prénoms et la date de naissance sont obligatoires')
            return redirect('employes:detail', pk=employe.id)
        
        enfant_id = request.POST.get('enfant_id')
        
        if enfant_id:
            # Modification
            enfant = get_object_or_404(EnfantEmploye, pk=enfant_id, employe=employe)
        else:
            # Création
            enfant = EnfantEmploye(employe=employe)
        
        enfant.nom = nom
        enfant.prenoms = prenoms
        enfant.date_naissance = date_naissance
        enfant.sexe = request.POST.get('sexe') or None
        enfant.lieu_naissance = request.POST.get('lieu_naissance', '')
        enfant.scolarise = 'scolarise' in request.POST
        enfant.etablissement_scolaire = request.POST.get('etablissement_scolaire', '')
        
        if 'acte_naissance' in request.FILES:
            enfant.acte_naissance = request.FILES['acte_naissance']
        if 'certificat_scolarite' in request.FILES:
            enfant.certificat_scolarite = request.FILES['certificat_scolarite']
        
        enfant.save()
        
        # Mettre à jour le nombre d'enfants
        employe.nombre_enfants = employe.enfants.count()
        employe.save(update_fields=['nombre_enfants'])
        
        log_activity(
            request,
            f"{'Modification' if enfant_id else 'Ajout'} enfant {enfant.nom} pour {employe.matricule}",
            'employes',
            'employes',
            employe.id
        )
        
        messages.success(request, f'Enfant {enfant.nom} {enfant.prenoms} enregistré avec succès')
    
    return redirect('employes:detail', pk=employe.id)


@login_required
def supprimer_enfant(request, enfant_id):
    """Supprimer un enfant d'un employé"""
    enfant = get_object_or_404(EnfantEmploye, pk=enfant_id, employe__entreprise=request.user.entreprise)
    employe = enfant.employe
    nom_enfant = f"{enfant.nom} {enfant.prenoms}"
    
    enfant.delete()
    
    # Mettre à jour le nombre d'enfants
    employe.nombre_enfants = employe.enfants.count()
    employe.save(update_fields=['nombre_enfants'])
    
    log_activity(
        request,
        f"Suppression enfant {nom_enfant} pour {employe.matricule}",
        'employes',
        'employes',
        employe.id
    )
    
    messages.success(request, f'Enfant {nom_enfant} supprimé avec succès')
    return redirect('employes:detail', pk=employe.id)
