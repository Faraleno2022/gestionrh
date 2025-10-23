from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, date
import random
import string

from .models import OffreEmploi, Candidature, EntretienRecrutement
from core.models import Poste, Service
from employes.models import Employe


@login_required
def recrutement_home(request):
    """Vue d'accueil du module recrutement"""
    # Statistiques
    stats = {
        'offres_ouvertes': OffreEmploi.objects.filter(statut_offre='ouverte').count(),
        'candidatures_recues': Candidature.objects.filter(statut_candidature='recue').count(),
        'entretiens_prevus': EntretienRecrutement.objects.filter(
            date_entretien__gte=timezone.now()
        ).count(),
        'candidatures_retenues': Candidature.objects.filter(statut_candidature='retenue').count(),
    }
    
    # Offres récentes
    offres_recentes = OffreEmploi.objects.filter(statut_offre='ouverte')[:5]
    
    # Candidatures récentes
    candidatures_recentes = Candidature.objects.all()[:5]
    
    # Prochains entretiens
    prochains_entretiens = EntretienRecrutement.objects.filter(
        date_entretien__gte=timezone.now()
    ).order_by('date_entretien')[:5]
    
    return render(request, 'recrutement/home.html', {
        'stats': stats,
        'offres_recentes': offres_recentes,
        'candidatures_recentes': candidatures_recentes,
        'prochains_entretiens': prochains_entretiens
    })


# ============= OFFRES D'EMPLOI =============

@login_required
def liste_offres(request):
    """Liste des offres d'emploi"""
    statut = request.GET.get('statut')
    service_id = request.GET.get('service')
    
    offres = OffreEmploi.objects.all().select_related('poste', 'service', 'responsable_recrutement')
    
    if statut:
        offres = offres.filter(statut_offre=statut)
    if service_id:
        offres = offres.filter(service_id=service_id)
    
    # Ajouter le nombre de candidatures pour chaque offre
    offres = offres.annotate(nb_candidatures=Count('candidatures'))
    
    services = Service.objects.all()
    
    return render(request, 'recrutement/offres/liste.html', {
        'offres': offres,
        'services': services
    })


@login_required
def creer_offre(request):
    """Créer une offre d'emploi"""
    if request.method == 'POST':
        try:
            # Générer une référence unique
            reference = f"OFF-{date.today().year}-{''.join(random.choices(string.digits, k=4))}"
            
            offre = OffreEmploi.objects.create(
                reference_offre=reference,
                intitule_poste=request.POST.get('intitule_poste'),
                poste_id=request.POST.get('poste') if request.POST.get('poste') else None,
                service_id=request.POST.get('service') if request.POST.get('service') else None,
                type_contrat=request.POST.get('type_contrat'),
                nombre_postes=request.POST.get('nombre_postes', 1),
                date_limite_candidature=request.POST.get('date_limite') if request.POST.get('date_limite') else None,
                description_poste=request.POST.get('description'),
                profil_recherche=request.POST.get('profil'),
                competences_requises=request.POST.get('competences'),
                experience_requise=request.POST.get('experience') if request.POST.get('experience') else None,
                formation_requise=request.POST.get('formation'),
                salaire_propose_min=request.POST.get('salaire_min') if request.POST.get('salaire_min') else None,
                salaire_propose_max=request.POST.get('salaire_max') if request.POST.get('salaire_max') else None,
                avantages=request.POST.get('avantages'),
                responsable_recrutement_id=request.POST.get('responsable') if request.POST.get('responsable') else None,
                statut_offre='ouverte'
            )
            
            messages.success(request, f'Offre {reference} créée avec succès.')
            return redirect('recrutement:detail_offre', pk=offre.pk)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création : {str(e)}')
    
    postes = Poste.objects.filter(actif=True)
    services = Service.objects.filter(actif=True)
    employes = Employe.objects.filter(statut_employe='actif')
    
    return render(request, 'recrutement/offres/creer.html', {
        'postes': postes,
        'services': services,
        'employes': employes
    })


@login_required
def detail_offre(request, pk):
    """Détail d'une offre d'emploi"""
    offre = get_object_or_404(OffreEmploi, pk=pk)
    candidatures = offre.candidatures.all()
    
    # Statistiques des candidatures
    stats_candidatures = {
        'total': candidatures.count(),
        'recues': candidatures.filter(statut_candidature='recue').count(),
        'preselectionnes': candidatures.filter(statut_candidature='preselectionne').count(),
        'entretien': candidatures.filter(statut_candidature='entretien').count(),
        'retenues': candidatures.filter(statut_candidature='retenue').count(),
        'rejetees': candidatures.filter(statut_candidature='rejetee').count(),
    }
    
    return render(request, 'recrutement/offres/detail.html', {
        'offre': offre,
        'candidatures': candidatures,
        'stats': stats_candidatures
    })


@login_required
def modifier_offre(request, pk):
    """Modifier une offre d'emploi"""
    offre = get_object_or_404(OffreEmploi, pk=pk)
    
    if request.method == 'POST':
        try:
            offre.intitule_poste = request.POST.get('intitule_poste')
            offre.poste_id = request.POST.get('poste') if request.POST.get('poste') else None
            offre.service_id = request.POST.get('service') if request.POST.get('service') else None
            offre.type_contrat = request.POST.get('type_contrat')
            offre.nombre_postes = request.POST.get('nombre_postes', 1)
            offre.date_limite_candidature = request.POST.get('date_limite') if request.POST.get('date_limite') else None
            offre.description_poste = request.POST.get('description')
            offre.profil_recherche = request.POST.get('profil')
            offre.competences_requises = request.POST.get('competences')
            offre.experience_requise = request.POST.get('experience') if request.POST.get('experience') else None
            offre.formation_requise = request.POST.get('formation')
            offre.salaire_propose_min = request.POST.get('salaire_min') if request.POST.get('salaire_min') else None
            offre.salaire_propose_max = request.POST.get('salaire_max') if request.POST.get('salaire_max') else None
            offre.avantages = request.POST.get('avantages')
            offre.statut_offre = request.POST.get('statut')
            offre.save()
            
            messages.success(request, 'Offre modifiée avec succès.')
            return redirect('recrutement:detail_offre', pk=offre.pk)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification : {str(e)}')
    
    postes = Poste.objects.filter(actif=True)
    services = Service.objects.filter(actif=True)
    
    return render(request, 'recrutement/offres/modifier.html', {
        'offre': offre,
        'postes': postes,
        'services': services
    })


# ============= CANDIDATURES =============

@login_required
def liste_candidatures(request):
    """Liste des candidatures"""
    statut = request.GET.get('statut')
    offre_id = request.GET.get('offre')
    
    candidatures = Candidature.objects.all().select_related('offre')
    
    if statut:
        candidatures = candidatures.filter(statut_candidature=statut)
    if offre_id:
        candidatures = candidatures.filter(offre_id=offre_id)
    
    offres = OffreEmploi.objects.filter(statut_offre='ouverte')
    
    return render(request, 'recrutement/candidatures/liste.html', {
        'candidatures': candidatures,
        'offres': offres
    })


@login_required
def creer_candidature(request):
    """Créer une candidature"""
    if request.method == 'POST':
        try:
            # Générer un numéro unique
            numero = f"CAND-{date.today().year}-{''.join(random.choices(string.digits, k=5))}"
            
            candidature = Candidature.objects.create(
                offre_id=request.POST.get('offre'),
                numero_candidature=numero,
                civilite=request.POST.get('civilite'),
                nom=request.POST.get('nom'),
                prenoms=request.POST.get('prenoms'),
                date_naissance=request.POST.get('date_naissance') if request.POST.get('date_naissance') else None,
                nationalite=request.POST.get('nationalite'),
                telephone=request.POST.get('telephone'),
                email=request.POST.get('email'),
                adresse=request.POST.get('adresse'),
                formation_niveau=request.POST.get('formation'),
                experience_annees=request.POST.get('experience') if request.POST.get('experience') else None,
                statut_candidature='recue'
            )
            
            # Gérer les fichiers
            if request.FILES.get('cv'):
                candidature.cv_fichier = request.FILES['cv']
            if request.FILES.get('lettre'):
                candidature.lettre_motivation = request.FILES['lettre']
            candidature.save()
            
            messages.success(request, f'Candidature {numero} enregistrée avec succès.')
            return redirect('recrutement:detail_candidature', pk=candidature.pk)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'enregistrement : {str(e)}')
    
    offres = OffreEmploi.objects.filter(statut_offre='ouverte')
    
    return render(request, 'recrutement/candidatures/creer.html', {
        'offres': offres
    })


@login_required
def detail_candidature(request, pk):
    """Détail d'une candidature"""
    candidature = get_object_or_404(Candidature, pk=pk)
    entretiens = candidature.entretiens.all()
    
    return render(request, 'recrutement/candidatures/detail.html', {
        'candidature': candidature,
        'entretiens': entretiens
    })


@login_required
def evaluer_candidature(request, pk):
    """Évaluer une candidature"""
    candidature = get_object_or_404(Candidature, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'preselectionner':
            candidature.statut_candidature = 'preselectionne'
            messages.success(request, 'Candidature présélectionnée.')
        elif action == 'convoquer':
            candidature.statut_candidature = 'entretien'
            messages.success(request, 'Candidat convoqué en entretien.')
        elif action == 'retenir':
            candidature.statut_candidature = 'retenue'
            messages.success(request, 'Candidature retenue.')
        elif action == 'rejeter':
            candidature.statut_candidature = 'rejetee'
            messages.success(request, 'Candidature rejetée.')
        
        candidature.score_evaluation = request.POST.get('score') if request.POST.get('score') else None
        candidature.commentaires = request.POST.get('commentaires')
        candidature.save()
        
        return redirect('recrutement:detail_candidature', pk=candidature.pk)
    
    return render(request, 'recrutement/candidatures/evaluer.html', {
        'candidature': candidature
    })


# ============= ENTRETIENS =============

@login_required
def liste_entretiens(request):
    """Liste des entretiens"""
    entretiens = EntretienRecrutement.objects.all().select_related('candidature', 'candidature__offre')
    
    return render(request, 'recrutement/entretiens/liste.html', {
        'entretiens': entretiens
    })


@login_required
def creer_entretien(request, candidature_id):
    """Planifier un entretien"""
    candidature = get_object_or_404(Candidature, pk=candidature_id)
    
    if request.method == 'POST':
        try:
            entretien = EntretienRecrutement.objects.create(
                candidature=candidature,
                type_entretien=request.POST.get('type_entretien'),
                date_entretien=request.POST.get('date_entretien'),
                lieu_entretien=request.POST.get('lieu'),
                intervieweurs=request.POST.get('intervieweurs'),
                duree_minutes=request.POST.get('duree') if request.POST.get('duree') else None
            )
            
            # Mettre à jour le statut de la candidature
            candidature.statut_candidature = 'entretien'
            candidature.date_entretien = request.POST.get('date_entretien')
            candidature.save()
            
            messages.success(request, 'Entretien planifié avec succès.')
            return redirect('recrutement:detail_entretien', pk=entretien.pk)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la planification : {str(e)}')
    
    return render(request, 'recrutement/entretiens/creer.html', {
        'candidature': candidature
    })


@login_required
def detail_entretien(request, pk):
    """Détail d'un entretien"""
    entretien = get_object_or_404(EntretienRecrutement, pk=pk)
    
    return render(request, 'recrutement/entretiens/detail.html', {
        'entretien': entretien
    })


@login_required
def evaluer_entretien(request, pk):
    """Évaluer un entretien"""
    entretien = get_object_or_404(EntretienRecrutement, pk=pk)
    
    if request.method == 'POST':
        try:
            entretien.evaluation_technique = request.POST.get('eval_technique') if request.POST.get('eval_technique') else None
            entretien.evaluation_comportementale = request.POST.get('eval_comportementale') if request.POST.get('eval_comportementale') else None
            entretien.evaluation_motivation = request.POST.get('eval_motivation') if request.POST.get('eval_motivation') else None
            
            # Calculer la note globale
            if all([entretien.evaluation_technique, entretien.evaluation_comportementale, entretien.evaluation_motivation]):
                entretien.note_globale = round(
                    (int(entretien.evaluation_technique) + 
                     int(entretien.evaluation_comportementale) + 
                     int(entretien.evaluation_motivation)) / 3
                )
            
            entretien.decision = request.POST.get('decision')
            entretien.commentaires = request.POST.get('commentaires')
            entretien.recommandations = request.POST.get('recommandations')
            entretien.save()
            
            messages.success(request, 'Évaluation enregistrée avec succès.')
            return redirect('recrutement:detail_entretien', pk=entretien.pk)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'évaluation : {str(e)}')
    
    return render(request, 'recrutement/entretiens/evaluer.html', {
        'entretien': entretien
    })
