from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import datetime, date
import random
import string

from .models import CatalogueFormation, SessionFormation, InscriptionFormation, EvaluationFormation, PlanFormation
from employes.models import Employe
from core.decorators import entreprise_active_required


@login_required
@entreprise_active_required
def formation_home(request):
    """Vue d'accueil du module formation"""
    # Statistiques
    stats = {
        'total_formations': CatalogueFormation.objects.filter(
            entreprise=request.user.entreprise,
            actif=True
        ).count(),
        'sessions_planifiees': SessionFormation.objects.filter(
            formation__entreprise=request.user.entreprise,
            statut='planifiee'
        ).count(),
        'sessions_en_cours': SessionFormation.objects.filter(
            formation__entreprise=request.user.entreprise,
            statut='en_cours'
        ).count(),
        'total_participants': InscriptionFormation.objects.filter(
            session__formation__entreprise=request.user.entreprise,
            statut__in=['inscrit', 'confirme', 'present']
        ).count(),
    }
    
    # Plan de formation en cours
    annee_actuelle = date.today().year
    plan_actuel = PlanFormation.objects.filter(
        entreprise=request.user.entreprise,
        annee=annee_actuelle
    ).first()
    
    # Prochaines sessions
    prochaines_sessions = SessionFormation.objects.filter(
        date_debut__gte=date.today(),
        statut='planifiee',
        formation__entreprise=request.user.entreprise,
    ).select_related('formation').order_by('date_debut')[:5]
    
    # Formations populaires
    formations_populaires = CatalogueFormation.objects.annotate(
        nb_sessions=Count('sessions')
    ).filter(
        entreprise=request.user.entreprise,
        actif=True
    ).order_by('-nb_sessions')[:5]
    
    return render(request, 'formation/home.html', {
        'stats': stats,
        'plan_actuel': plan_actuel,
        'prochaines_sessions': prochaines_sessions,
        'formations_populaires': formations_populaires
    })


# ============= CATALOGUE =============

@login_required
@entreprise_active_required
def liste_catalogue(request):
    """Liste des formations du catalogue"""
    type_formation = request.GET.get('type')
    domaine = request.GET.get('domaine')
    
    formations = CatalogueFormation.objects.filter(
        entreprise=request.user.entreprise
    ).annotate(
        nb_sessions=Count('sessions')
    )
    
    if type_formation:
        formations = formations.filter(type_formation=type_formation)
    if domaine:
        formations = formations.filter(domaine=domaine)
    
    return render(request, 'formation/catalogue/liste.html', {
        'formations': formations
    })


@login_required
@entreprise_active_required
def creer_formation(request):
    """Créer une formation"""
    if request.method == 'POST':
        try:
            # Générer un code unique
            code = f"FORM-{''.join(random.choices(string.digits, k=3))}"
            
            formation = CatalogueFormation.objects.create(
                entreprise=request.user.entreprise,
                code_formation=code,
                intitule=request.POST.get('intitule'),
                type_formation=request.POST.get('type_formation'),
                domaine=request.POST.get('domaine'),
                description=request.POST.get('description'),
                objectifs=request.POST.get('objectifs'),
                contenu=request.POST.get('contenu'),
                duree_jours=request.POST.get('duree_jours'),
                duree_heures=request.POST.get('duree_heures'),
                prerequis=request.POST.get('prerequis'),
                organisme_formateur=request.POST.get('organisme'),
                cout_unitaire=request.POST.get('cout') if request.POST.get('cout') else None,
                actif=True
            )
            
            messages.success(request, f'Formation {code} créée avec succès.')
            return redirect('formation:detail_formation', pk=formation.pk)
            
        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')
    
    return render(request, 'formation/catalogue/creer.html')


@login_required
@entreprise_active_required
def detail_formation(request, pk):
    """Détail d'une formation"""
    formation = get_object_or_404(CatalogueFormation, pk=pk, entreprise=request.user.entreprise)
    sessions = formation.sessions.all().annotate(
        nb_inscrits=Count('inscriptions')
    )
    
    return render(request, 'formation/catalogue/detail.html', {
        'formation': formation,
        'sessions': sessions
    })


@login_required
@entreprise_active_required
def modifier_formation(request, pk):
    """Modifier une formation"""
    formation = get_object_or_404(CatalogueFormation, pk=pk, entreprise=request.user.entreprise)
    
    if request.method == 'POST':
        try:
            formation.intitule = request.POST.get('intitule')
            formation.type_formation = request.POST.get('type_formation')
            formation.domaine = request.POST.get('domaine')
            formation.description = request.POST.get('description')
            formation.objectifs = request.POST.get('objectifs')
            formation.contenu = request.POST.get('contenu')
            formation.duree_jours = request.POST.get('duree_jours')
            formation.duree_heures = request.POST.get('duree_heures')
            formation.prerequis = request.POST.get('prerequis')
            formation.organisme_formateur = request.POST.get('organisme')
            formation.cout_unitaire = request.POST.get('cout') if request.POST.get('cout') else None
            formation.save()
            
            messages.success(request, 'Formation modifiée avec succès.')
            return redirect('formation:detail_formation', pk=formation.pk)
            
        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')
    
    return render(request, 'formation/catalogue/modifier.html', {
        'formation': formation
    })


# ============= SESSIONS =============

@login_required
@entreprise_active_required
def liste_sessions(request):
    """Liste des sessions"""
    statut = request.GET.get('statut')
    
    sessions = SessionFormation.objects.filter(
        formation__entreprise=request.user.entreprise
    ).select_related('formation').annotate(
        nb_inscrits=Count('inscriptions')
    )
    
    if statut:
        sessions = sessions.filter(statut=statut)
    
    return render(request, 'formation/sessions/liste.html', {
        'sessions': sessions
    })


@login_required
@entreprise_active_required
def planifier_session(request):
    """Planifier une session"""
    if request.method == 'POST':
        try:
            # Générer une référence unique
            reference = f"SESS-{date.today().year}-{''.join(random.choices(string.digits, k=3))}"
            
            formation = get_object_or_404(
                CatalogueFormation,
                pk=request.POST.get('formation'),
                entreprise=request.user.entreprise,
            )

            session = SessionFormation.objects.create(
                formation=formation,
                reference_session=reference,
                date_debut=request.POST.get('date_debut'),
                date_fin=request.POST.get('date_fin'),
                lieu=request.POST.get('lieu'),
                formateur=request.POST.get('formateur'),
                nombre_places=request.POST.get('nombre_places', 10),
                cout_total=request.POST.get('cout_total') if request.POST.get('cout_total') else None,
                statut='planifiee'
            )
            
            messages.success(request, f'Session {reference} planifiée avec succès.')
            return redirect('formation:detail_session', pk=session.pk)
            
        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')
    
    formations = CatalogueFormation.objects.filter(
        entreprise=request.user.entreprise,
        actif=True
    )
    
    return render(request, 'formation/sessions/planifier.html', {
        'formations': formations
    })


@login_required
@entreprise_active_required
def detail_session(request, pk):
    """Détail d'une session"""
    session = get_object_or_404(SessionFormation, pk=pk, formation__entreprise=request.user.entreprise)
    inscriptions = session.inscriptions.all().select_related('employe')
    
    return render(request, 'formation/sessions/detail.html', {
        'session': session,
        'inscriptions': inscriptions
    })


@login_required
@entreprise_active_required
def inscrire_employe(request, session_id):
    """Inscrire un employé à une session"""
    session = get_object_or_404(SessionFormation, pk=session_id, formation__entreprise=request.user.entreprise)
    
    if request.method == 'POST':
        try:
            employe_id = request.POST.get('employe')
            employe = get_object_or_404(Employe, pk=employe_id, entreprise=request.user.entreprise)
            
            # Vérifier les places disponibles
            if session.nombre_inscrits >= session.nombre_places:
                messages.error(request, 'Plus de places disponibles.')
                return redirect('formation:detail_session', pk=session.pk)
            
            # Créer l'inscription
            inscription = InscriptionFormation.objects.create(
                session=session,
                employe=employe,
                statut='inscrit'
            )
            
            # Mettre à jour le nombre d'inscrits
            session.nombre_inscrits += 1
            session.save()
            
            messages.success(request, 'Employé inscrit avec succès.')
            return redirect('formation:detail_session', pk=session.pk)
            
        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')
    
    employes = Employe.objects.filter(
        entreprise=request.user.entreprise,
        statut_employe='actif'
    )
    
    return render(request, 'formation/inscriptions/inscrire.html', {
        'session': session,
        'employes': employes
    })


# ============= INSCRIPTIONS =============

@login_required
@entreprise_active_required
def liste_inscriptions(request):
    """Liste des inscriptions"""
    inscriptions = InscriptionFormation.objects.filter(
        session__formation__entreprise=request.user.entreprise,
        employe__entreprise=request.user.entreprise,
    ).select_related(
        'employe', 'session', 'session__formation'
    )
    
    return render(request, 'formation/inscriptions/liste.html', {
        'inscriptions': inscriptions
    })


@login_required
@entreprise_active_required
def evaluer_participant(request, pk):
    """Évaluer un participant"""
    inscription = get_object_or_404(
        InscriptionFormation,
        pk=pk,
        session__formation__entreprise=request.user.entreprise,
        employe__entreprise=request.user.entreprise,
    )
    
    if request.method == 'POST':
        try:
            inscription.note_evaluation = request.POST.get('note') if request.POST.get('note') else None
            inscription.appreciation = request.POST.get('appreciation')
            inscription.certificat_obtenu = request.POST.get('certificat') == 'on'
            inscription.commentaires = request.POST.get('commentaires')
            inscription.statut = 'present'
            inscription.save()
            
            messages.success(request, 'Évaluation enregistrée avec succès.')
            return redirect('formation:detail_session', pk=inscription.session.pk)
            
        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')
    
    return render(request, 'formation/inscriptions/evaluer.html', {
        'inscription': inscription
    })


# ============= ÉVALUATIONS =============

@login_required
@entreprise_active_required
def formulaire_evaluation(request, inscription_id):
    """Formulaire d'évaluation de la formation"""
    inscription = get_object_or_404(
        InscriptionFormation,
        pk=inscription_id,
        session__formation__entreprise=request.user.entreprise,
        employe__entreprise=request.user.entreprise,
    )
    
    if request.method == 'POST':
        try:
            evaluation = EvaluationFormation.objects.create(
                inscription=inscription,
                note_contenu=request.POST.get('note_contenu'),
                note_formateur=request.POST.get('note_formateur'),
                note_organisation=request.POST.get('note_organisation'),
                note_moyens=request.POST.get('note_moyens'),
                note_globale=request.POST.get('note_globale'),
                points_forts=request.POST.get('points_forts'),
                points_ameliorer=request.POST.get('points_ameliorer'),
                suggestions=request.POST.get('suggestions'),
                competences_acquises=request.POST.get('competences'),
                application_travail=request.POST.get('application') == 'on',
                recommandation=request.POST.get('recommandation') == 'on'
            )
            
            messages.success(request, 'Évaluation enregistrée. Merci pour votre retour !')
            return redirect('formation:home')
            
        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')
    
    return render(request, 'formation/evaluations/formulaire.html', {
        'inscription': inscription
    })


@login_required
@entreprise_active_required
def liste_evaluations(request):
    """Liste des évaluations"""
    evaluations = EvaluationFormation.objects.filter(
        inscription__session__formation__entreprise=request.user.entreprise,
        inscription__employe__entreprise=request.user.entreprise,
    ).select_related(
        'inscription', 'inscription__employe', 'inscription__session__formation'
    )
    
    return render(request, 'formation/evaluations/liste.html', {
        'evaluations': evaluations
    })


# ============= PLAN DE FORMATION =============

@login_required
@entreprise_active_required
def liste_plans(request):
    """Liste des plans de formation"""
    plans = PlanFormation.objects.filter(entreprise=request.user.entreprise)
    
    return render(request, 'formation/plan/liste.html', {
        'plans': plans
    })


@login_required
@entreprise_active_required
def creer_plan(request):
    """Créer un plan de formation"""
    if request.method == 'POST':
        try:
            plan = PlanFormation.objects.create(
                entreprise=request.user.entreprise,
                annee=request.POST.get('annee'),
                budget_total=request.POST.get('budget_total'),
                objectifs=request.POST.get('objectifs'),
                statut='brouillon'
            )
            
            messages.success(request, f'Plan de formation {plan.annee} créé avec succès.')
            return redirect('formation:detail_plan', annee=plan.annee)
            
        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')
    
    return render(request, 'formation/plan/creer.html')


@login_required
@entreprise_active_required
def detail_plan(request, annee):
    """Détail d'un plan de formation"""
    plan = get_object_or_404(PlanFormation, annee=annee, entreprise=request.user.entreprise)
    
    # Sessions de l'année
    sessions = SessionFormation.objects.filter(
        date_debut__year=annee,
        formation__entreprise=request.user.entreprise,
    ).select_related('formation')
    
    return render(request, 'formation/plan/detail.html', {
        'plan': plan,
        'sessions': sessions
    })
