from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, Avg
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from datetime import datetime, date, timedelta, time
import json
import calendar

from .models import (
    Pointage, Conge, SoldeConge, Absence, ArretTravail,
    HoraireTravail, AffectationHoraire, JourFerie
)
from employes.models import Employe


@login_required
def temps_travail_home(request):
    """Vue d'accueil du module temps de travail"""
    today = date.today()
    
    # Statistiques du jour
    stats = {
        'total_employes': Employe.objects.filter(statut_employe='Actif').count(),
        'presents_aujourdhui': Pointage.objects.filter(
            date_pointage=today,
            statut_pointage='present'
        ).count(),
        'absents_aujourdhui': Pointage.objects.filter(
            date_pointage=today,
            statut_pointage='absent'
        ).count(),
        'en_conge': Conge.objects.filter(
            date_debut__lte=today,
            date_fin__gte=today,
            statut_demande='approuve'
        ).count(),
        'demandes_conge_attente': Conge.objects.filter(
            statut_demande='en_attente'
        ).count(),
    }
    
    # Taux de présence
    if stats['total_employes'] > 0:
        stats['taux_presence'] = round(
            (stats['presents_aujourdhui'] / stats['total_employes']) * 100, 1
        )
    else:
        stats['taux_presence'] = 0
    
    # Prochains jours fériés
    prochains_feries = JourFerie.objects.filter(
        date_jour_ferie__gte=today
    ).order_by('date_jour_ferie')[:5]
    
    return render(request, 'temps_travail/home.html', {
        'stats': stats,
        'prochains_feries': prochains_feries
    })


# ============= POINTAGES =============

@login_required
def liste_pointages(request):
    """Liste des pointages"""
    # Filtres
    date_filter = request.GET.get('date', date.today().isoformat())
    employe_id = request.GET.get('employe')
    statut = request.GET.get('statut')
    
    try:
        date_pointage = datetime.strptime(date_filter, '%Y-%m-%d').date()
    except:
        date_pointage = date.today()
    
    pointages = Pointage.objects.filter(date_pointage=date_pointage).select_related('employe')
    
    if employe_id:
        pointages = pointages.filter(employe_id=employe_id)
    if statut:
        pointages = pointages.filter(statut_pointage=statut)
    
    # Statistiques du jour
    stats = pointages.aggregate(
        total=Count('id'),
        presents=Count('id', filter=Q(statut_pointage='present')),
        absents=Count('id', filter=Q(statut_pointage='absent')),
        retards=Count('id', filter=Q(statut_pointage='retard')),
        heures_sup_total=Sum('heures_supplementaires')
    )
    
    employes = Employe.objects.filter(statut_employe='Actif')
    
    return render(request, 'temps_travail/pointages/liste.html', {
        'pointages': pointages,
        'date_pointage': date_pointage,
        'stats': stats,
        'employes': employes
    })


@login_required
def creer_pointage(request):
    """Créer un pointage"""
    if request.method == 'POST':
        try:
            employe_id = request.POST.get('employe')
            date_pointage = request.POST.get('date_pointage')
            heure_entree = request.POST.get('heure_entree')
            heure_sortie = request.POST.get('heure_sortie')
            statut = request.POST.get('statut', 'present')
            
            employe = get_object_or_404(Employe, pk=employe_id)
            
            # Vérifier si le pointage existe déjà
            if Pointage.objects.filter(employe=employe, date_pointage=date_pointage).exists():
                messages.error(request, 'Un pointage existe déjà pour cet employé à cette date.')
                return redirect('temps_travail:liste_pointages')
            
            # Calculer les heures travaillées
            heures_travaillees = None
            heures_supplementaires = Decimal('0')
            
            if heure_entree and heure_sortie:
                entree = datetime.strptime(heure_entree, '%H:%M').time()
                sortie = datetime.strptime(heure_sortie, '%H:%M').time()
                
                # Calculer la durée
                debut = datetime.combine(date.today(), entree)
                fin = datetime.combine(date.today(), sortie)
                duree = (fin - debut).total_seconds() / 3600
                
                heures_travaillees = Decimal(str(duree))
                
                # Calculer les heures supplémentaires (> 8h)
                if heures_travaillees > 8:
                    heures_supplementaires = heures_travaillees - Decimal('8')
            
            # Créer le pointage
            pointage = Pointage.objects.create(
                employe=employe,
                date_pointage=date_pointage,
                heure_entree=heure_entree if heure_entree else None,
                heure_sortie=heure_sortie if heure_sortie else None,
                heures_travaillees=heures_travaillees,
                heures_supplementaires=heures_supplementaires,
                statut_pointage=statut,
                observations=request.POST.get('observations', '')
            )
            
            messages.success(request, 'Pointage créé avec succès.')
            return redirect('temps_travail:liste_pointages')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création : {str(e)}')
    
    employes = Employe.objects.filter(statut_employe='Actif')
    return render(request, 'temps_travail/pointages/creer.html', {
        'employes': employes,
        'date_defaut': date.today().isoformat()
    })


@login_required
def pointer_entree(request):
    """Pointer l'entrée d'un employé"""
    if request.method == 'POST':
        try:
            employe_id = request.POST.get('employe')
            employe = get_object_or_404(Employe, pk=employe_id)
            today = date.today()
            now = timezone.now().time()
            
            # Vérifier si un pointage existe déjà
            pointage, created = Pointage.objects.get_or_create(
                employe=employe,
                date_pointage=today,
                defaults={
                    'heure_entree': now,
                    'statut_pointage': 'present'
                }
            )
            
            if not created:
                if pointage.heure_entree:
                    messages.warning(request, 'Entrée déjà pointée aujourd\'hui.')
                else:
                    pointage.heure_entree = now
                    pointage.statut_pointage = 'present'
                    pointage.save()
                    messages.success(request, 'Entrée pointée avec succès.')
            else:
                messages.success(request, 'Entrée pointée avec succès.')
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


@login_required
def pointer_sortie(request):
    """Pointer la sortie d'un employé"""
    if request.method == 'POST':
        try:
            employe_id = request.POST.get('employe')
            employe = get_object_or_404(Employe, pk=employe_id)
            today = date.today()
            now = timezone.now().time()
            
            pointage = Pointage.objects.filter(
                employe=employe,
                date_pointage=today
            ).first()
            
            if not pointage:
                return JsonResponse({'success': False, 'error': 'Aucune entrée pointée'})
            
            if pointage.heure_sortie:
                return JsonResponse({'success': False, 'error': 'Sortie déjà pointée'})
            
            pointage.heure_sortie = now
            
            # Calculer les heures travaillées
            if pointage.heure_entree:
                debut = datetime.combine(today, pointage.heure_entree)
                fin = datetime.combine(today, now)
                duree = (fin - debut).total_seconds() / 3600
                pointage.heures_travaillees = Decimal(str(duree))
                
                # Heures supplémentaires
                if pointage.heures_travaillees > 8:
                    pointage.heures_supplementaires = pointage.heures_travaillees - Decimal('8')
            
            pointage.save()
            messages.success(request, 'Sortie pointée avec succès.')
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


# ============= CONGÉS =============

@login_required
def liste_conges(request):
    """Liste des congés"""
    # Filtres
    statut = request.GET.get('statut')
    employe_id = request.GET.get('employe')
    annee = request.GET.get('annee', date.today().year)
    
    conges = Conge.objects.all().select_related('employe', 'approbateur')
    
    if statut:
        conges = conges.filter(statut_demande=statut)
    if employe_id:
        conges = conges.filter(employe_id=employe_id)
    if annee:
        conges = conges.filter(date_debut__year=annee)
    
    employes = Employe.objects.filter(statut_employe='Actif')
    annees = range(date.today().year - 2, date.today().year + 2)
    
    return render(request, 'temps_travail/conges/liste.html', {
        'conges': conges,
        'employes': employes,
        'annees': annees
    })


@login_required
def creer_conge(request):
    """Créer une demande de congé"""
    if request.method == 'POST':
        try:
            employe_id = request.POST.get('employe')
            type_conge = request.POST.get('type_conge')
            date_debut = request.POST.get('date_debut')
            date_fin = request.POST.get('date_fin')
            motif = request.POST.get('motif', '')
            
            employe = get_object_or_404(Employe, pk=employe_id)
            
            # Calculer le nombre de jours
            debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
            fin = datetime.strptime(date_fin, '%Y-%m-%d').date()
            nombre_jours = (fin - debut).days + 1
            
            # Vérifier le solde de congés
            annee_ref = debut.year
            solde = SoldeConge.objects.filter(
                employe=employe,
                annee=annee_ref
            ).first()
            
            if type_conge == 'annuel' and solde:
                if solde.conges_restants < nombre_jours:
                    messages.error(
                        request,
                        f'Solde insuffisant. Disponible: {solde.conges_restants} jours'
                    )
                    return redirect('temps_travail:creer_conge')
            
            # Créer la demande
            conge = Conge.objects.create(
                employe=employe,
                type_conge=type_conge,
                date_debut=debut,
                date_fin=fin,
                nombre_jours=nombre_jours,
                annee_reference=annee_ref,
                motif=motif,
                statut_demande='en_attente'
            )
            
            messages.success(request, 'Demande de congé créée avec succès.')
            return redirect('temps_travail:liste_conges')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création : {str(e)}')
    
    employes = Employe.objects.filter(statut_employe='Actif')
    return render(request, 'temps_travail/conges/creer.html', {
        'employes': employes
    })


@login_required
def approuver_conge(request, pk):
    """Approuver une demande de congé"""
    conge = get_object_or_404(Conge, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        commentaire = request.POST.get('commentaire', '')
        
        if action == 'approuver':
            conge.statut_demande = 'approuve'
            conge.date_approbation = date.today()
            conge.commentaire_approbateur = commentaire
            conge.save()
            
            # Mettre à jour le solde
            if conge.type_conge == 'annuel':
                solde, created = SoldeConge.objects.get_or_create(
                    employe=conge.employe,
                    annee=conge.annee_reference,
                    defaults={'conges_acquis': Decimal('26')}
                )
                solde.conges_pris += conge.nombre_jours
                solde.conges_restants = solde.conges_acquis - solde.conges_pris + solde.conges_reports
                solde.save()
            
            messages.success(request, 'Congé approuvé avec succès.')
        
        elif action == 'rejeter':
            conge.statut_demande = 'rejete'
            conge.date_approbation = date.today()
            conge.commentaire_approbateur = commentaire
            conge.save()
            messages.success(request, 'Congé rejeté.')
        
        return redirect('temps_travail:liste_conges')
    
    return render(request, 'temps_travail/conges/approuver.html', {
        'conge': conge
    })


# ============= ABSENCES =============

@login_required
def liste_absences(request):
    """Liste des absences"""
    # Filtres
    employe_id = request.GET.get('employe')
    type_absence = request.GET.get('type')
    mois = request.GET.get('mois', date.today().month)
    annee = request.GET.get('annee', date.today().year)
    
    absences = Absence.objects.all().select_related('employe')
    
    if employe_id:
        absences = absences.filter(employe_id=employe_id)
    if type_absence:
        absences = absences.filter(type_absence=type_absence)
    if mois and annee:
        absences = absences.filter(
            date_absence__month=mois,
            date_absence__year=annee
        )
    
    employes = Employe.objects.filter(statut_employe='Actif')
    
    return render(request, 'temps_travail/absences/liste.html', {
        'absences': absences,
        'employes': employes
    })


@login_required
def creer_absence(request):
    """Enregistrer une absence"""
    if request.method == 'POST':
        try:
            employe_id = request.POST.get('employe')
            date_absence = request.POST.get('date_absence')
            type_absence = request.POST.get('type_absence')
            duree_jours = request.POST.get('duree_jours', 1)
            justifie = request.POST.get('justifie') == 'on'
            observations = request.POST.get('observations', '')
            
            employe = get_object_or_404(Employe, pk=employe_id)
            
            # Déterminer l'impact sur la paie
            impact_paie = 'paye'
            taux_maintien = Decimal('100')
            
            if type_absence == 'absence_injustifiee':
                impact_paie = 'non_paye'
                taux_maintien = Decimal('0')
            elif type_absence == 'maladie' and justifie:
                impact_paie = 'paye'
                taux_maintien = Decimal('100')
            
            absence = Absence.objects.create(
                employe=employe,
                date_absence=date_absence,
                type_absence=type_absence,
                duree_jours=duree_jours,
                justifie=justifie,
                impact_paie=impact_paie,
                taux_maintien_salaire=taux_maintien,
                observations=observations
            )
            
            messages.success(request, 'Absence enregistrée avec succès.')
            return redirect('temps_travail:liste_absences')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'enregistrement : {str(e)}')
    
    employes = Employe.objects.filter(statut_employe='Actif')
    return render(request, 'temps_travail/absences/creer.html', {
        'employes': employes
    })


# ============= JOURS FÉRIÉS =============

@login_required
def liste_jours_feries(request):
    """Liste des jours fériés"""
    annee = request.GET.get('annee', date.today().year)
    
    jours_feries = JourFerie.objects.filter(annee=annee)
    annees = range(date.today().year - 1, date.today().year + 3)
    
    return render(request, 'temps_travail/jours_feries/liste.html', {
        'jours_feries': jours_feries,
        'annee': int(annee),
        'annees': annees
    })


@login_required
def creer_jour_ferie(request):
    """Créer un jour férié"""
    if request.method == 'POST':
        try:
            libelle = request.POST.get('libelle')
            date_ferie = request.POST.get('date_ferie')
            type_ferie = request.POST.get('type_ferie')
            recurrent = request.POST.get('recurrent') == 'on'
            
            date_obj = datetime.strptime(date_ferie, '%Y-%m-%d').date()
            
            JourFerie.objects.create(
                libelle=libelle,
                date_jour_ferie=date_obj,
                annee=date_obj.year,
                type_ferie=type_ferie,
                recurrent=recurrent
            )
            
            messages.success(request, 'Jour férié créé avec succès.')
            return redirect('temps_travail:liste_jours_feries')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création : {str(e)}')
    
    return render(request, 'temps_travail/jours_feries/creer.html')


# ============= RAPPORTS =============

@login_required
def rapport_presence(request):
    """Rapport de présence"""
    # Filtres
    mois = int(request.GET.get('mois', date.today().month))
    annee = int(request.GET.get('annee', date.today().year))
    employe_id = request.GET.get('employe')
    
    # Dates du mois
    premier_jour = date(annee, mois, 1)
    dernier_jour = date(annee, mois, calendar.monthrange(annee, mois)[1])
    
    # Pointages du mois
    pointages = Pointage.objects.filter(
        date_pointage__gte=premier_jour,
        date_pointage__lte=dernier_jour
    ).select_related('employe')
    
    if employe_id:
        pointages = pointages.filter(employe_id=employe_id)
    
    # Statistiques par employé
    stats_employes = []
    employes = Employe.objects.filter(statut_employe='Actif')
    
    if employe_id:
        employes = employes.filter(pk=employe_id)
    
    for employe in employes:
        pointages_employe = pointages.filter(employe=employe)
        
        stats = {
            'employe': employe,
            'total_jours': pointages_employe.count(),
            'presents': pointages_employe.filter(statut_pointage='present').count(),
            'absents': pointages_employe.filter(statut_pointage='absent').count(),
            'retards': pointages_employe.filter(statut_pointage='retard').count(),
            'heures_travaillees': pointages_employe.aggregate(
                total=Sum('heures_travaillees')
            )['total'] or 0,
            'heures_supplementaires': pointages_employe.aggregate(
                total=Sum('heures_supplementaires')
            )['total'] or 0,
        }
        
        # Taux de présence
        jours_travailles = calendar.monthrange(annee, mois)[1]
        if jours_travailles > 0:
            stats['taux_presence'] = round(
                (stats['presents'] / jours_travailles) * 100, 1
            )
        else:
            stats['taux_presence'] = 0
        
        stats_employes.append(stats)
    
    mois_liste = [
        (1, 'Janvier'), (2, 'Février'), (3, 'Mars'), (4, 'Avril'),
        (5, 'Mai'), (6, 'Juin'), (7, 'Juillet'), (8, 'Août'),
        (9, 'Septembre'), (10, 'Octobre'), (11, 'Novembre'), (12, 'Décembre')
    ]
    annees = range(date.today().year - 2, date.today().year + 1)
    
    return render(request, 'temps_travail/rapports/presence.html', {
        'stats_employes': stats_employes,
        'mois': mois,
        'annee': annee,
        'mois_liste': mois_liste,
        'annees': annees,
        'employes': Employe.objects.filter(statut_employe='Actif')
    })


@login_required
def rapport_heures_supplementaires(request):
    """Rapport des heures supplémentaires"""
    mois = int(request.GET.get('mois', date.today().month))
    annee = int(request.GET.get('annee', date.today().year))
    
    premier_jour = date(annee, mois, 1)
    dernier_jour = date(annee, mois, calendar.monthrange(annee, mois)[1])
    
    # Pointages avec heures sup
    pointages = Pointage.objects.filter(
        date_pointage__gte=premier_jour,
        date_pointage__lte=dernier_jour,
        heures_supplementaires__gt=0
    ).select_related('employe').order_by('employe', 'date_pointage')
    
    # Totaux par employé
    totaux_employes = pointages.values('employe').annotate(
        total_heures_sup=Sum('heures_supplementaires'),
        nb_jours=Count('id')
    ).order_by('-total_heures_sup')
    
    # Enrichir avec les infos employé
    for total in totaux_employes:
        employe = Employe.objects.get(pk=total['employe'])
        total['employe_obj'] = employe
    
    mois_liste = [
        (1, 'Janvier'), (2, 'Février'), (3, 'Mars'), (4, 'Avril'),
        (5, 'Mai'), (6, 'Juin'), (7, 'Juillet'), (8, 'Août'),
        (9, 'Septembre'), (10, 'Octobre'), (11, 'Novembre'), (12, 'Décembre')
    ]
    annees = range(date.today().year - 2, date.today().year + 1)
    
    return render(request, 'temps_travail/rapports/heures_supplementaires.html', {
        'pointages': pointages,
        'totaux_employes': totaux_employes,
        'mois': mois,
        'annee': annee,
        'mois_liste': mois_liste,
        'annees': annees
    })
