from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta

from employes.models import Employe
from paie.models import BulletinPaie, PeriodePaie
from temps_travail.models import Conge, Pointage


@login_required
def index(request):
    """Tableau de bord principal"""
    context = {}
    
    # Statistiques employés
    employes_actifs = Employe.objects.filter(
        entreprise=request.user.entreprise,
        statut_employe='actif'
    )
    context['total_employes'] = employes_actifs.count()
    context['employes_hommes'] = employes_actifs.filter(sexe='M').count()
    context['employes_femmes'] = employes_actifs.filter(sexe='F').count()
    
    # Répartition par type de contrat
    context['employes_cdi'] = employes_actifs.filter(type_contrat='CDI').count()
    context['employes_cdd'] = employes_actifs.filter(type_contrat='CDD').count()
    context['employes_stage'] = employes_actifs.filter(type_contrat='Stage').count()
    
    # Congés en cours
    aujourd_hui = timezone.now().date()
    conges_en_cours = Conge.objects.filter(
        statut_demande='Approuvé',
        date_debut__lte=aujourd_hui,
        date_fin__gte=aujourd_hui,
        employe__entreprise=request.user.entreprise,
    )
    context['conges_en_cours'] = conges_en_cours.count()
    context['employes_en_conge'] = conges_en_cours.select_related('employe')[:5]
    
    # Congés en attente
    context['conges_en_attente'] = Conge.objects.filter(
        statut_demande='En attente',
        employe__entreprise=request.user.entreprise,
    ).count()
    
    # Paie du mois en cours
    mois_actuel = timezone.now().month
    annee_actuelle = timezone.now().year
    
    try:
        periode_actuelle = PeriodePaie.objects.get(
            entreprise=request.user.entreprise,
            annee=annee_actuelle,
            mois=mois_actuel
        )
        bulletins_mois = BulletinPaie.objects.filter(
            periode=periode_actuelle,
            employe__entreprise=request.user.entreprise,
        )
        context['bulletins_calcules'] = bulletins_mois.filter(statut_bulletin='Calculé').count()
        context['bulletins_valides'] = bulletins_mois.filter(statut_bulletin='Validé').count()
        context['masse_salariale'] = bulletins_mois.aggregate(
            total=Sum('net_a_payer')
        )['total'] or 0
    except PeriodePaie.DoesNotExist:
        context['bulletins_calcules'] = 0
        context['bulletins_valides'] = 0
        context['masse_salariale'] = 0
    
    # Pointages du jour
    context['pointages_jour'] = Pointage.objects.filter(
        date_pointage=aujourd_hui,
        employe__entreprise=request.user.entreprise,
    ).count()
    
    # Alertes
    context['alertes'] = []
    
    # Contrats arrivant à échéance (30 jours)
    date_limite = aujourd_hui + timedelta(days=30)
    contrats_echeance = Employe.objects.filter(
        entreprise=request.user.entreprise,
        type_contrat='CDD',
        date_fin_contrat__lte=date_limite,
        date_fin_contrat__gte=aujourd_hui,
        statut_employe='actif'
    ).count()
    
    if contrats_echeance > 0:
        context['alertes'].append({
            'type': 'warning',
            'icon': 'bi-exclamation-triangle',
            'message': f'{contrats_echeance} contrat(s) arrivent à échéance dans les 30 jours'
        })
    
    # Congés en attente de validation
    if context['conges_en_attente'] > 0:
        context['alertes'].append({
            'type': 'info',
            'icon': 'bi-calendar-check',
            'message': f'{context["conges_en_attente"]} demande(s) de congé en attente'
        })
    
    return render(request, 'dashboard/index.html', context)


@login_required
def rapports(request):
    """Page des rapports et statistiques"""
    context = {}
    
    # Statistiques annuelles
    annee = request.GET.get('annee', timezone.now().year)
    context['annee'] = int(annee)
    
    # Évolution effectif par mois
    effectif_mensuel = []
    for mois in range(1, 13):
        effectif = Employe.objects.filter(
            entreprise=request.user.entreprise,
            date_embauche__year__lte=annee,
            date_embauche__month__lte=mois
        ).exclude(
            date_depart__year__lt=annee
        ).exclude(
            date_depart__year=annee,
            date_depart__month__lt=mois
        ).count()
        effectif_mensuel.append(effectif)
    
    context['effectif_mensuel'] = effectif_mensuel
    context['mois'] = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 
                       'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc']
    
    # Pyramide des âges
    aujourd_hui = timezone.now().date()
    employes_actifs = Employe.objects.filter(
        entreprise=request.user.entreprise,
        statut_employe='actif'
    )
    
    pyramide_ages = {
        '< 25 ans': 0,
        '25-34 ans': 0,
        '35-44 ans': 0,
        '45-54 ans': 0,
        '55+ ans': 0
    }
    
    for employe in employes_actifs:
        if employe.date_naissance:
            age = (aujourd_hui - employe.date_naissance).days // 365
            if age < 25:
                pyramide_ages['< 25 ans'] += 1
            elif age < 35:
                pyramide_ages['25-34 ans'] += 1
            elif age < 45:
                pyramide_ages['35-44 ans'] += 1
            elif age < 55:
                pyramide_ages['45-54 ans'] += 1
            else:
                pyramide_ages['55+ ans'] += 1
    
    context['pyramide_ages'] = pyramide_ages
    
    # Répartition par service
    from core.models import Service
    services_stats = []
    for service in Service.objects.filter(
        actif=True,
        etablissement__societe__entreprise=request.user.entreprise,
    ):
        effectif = employes_actifs.filter(service=service).count()
        if effectif > 0:
            services_stats.append({
                'nom': service.nom_service,
                'effectif': effectif
            })
    
    context['services_stats'] = services_stats
    
    return render(request, 'dashboard/rapports.html', context)


@login_required
def statistiques_paie(request):
    """Statistiques de paie"""
    context = {}
    
    annee = request.GET.get('annee', timezone.now().year)
    context['annee'] = int(annee)
    
    # Masse salariale mensuelle
    masse_mensuelle = []
    for mois in range(1, 13):
        try:
            periode = PeriodePaie.objects.get(
                entreprise=request.user.entreprise,
                annee=annee,
                mois=mois
            )
            total = BulletinPaie.objects.filter(
                periode=periode,
                statut_bulletin__in=['Validé', 'Payé'],
                employe__entreprise=request.user.entreprise,
            ).aggregate(total=Sum('net_a_payer'))['total'] or 0
            masse_mensuelle.append(float(total))
        except PeriodePaie.DoesNotExist:
            masse_mensuelle.append(0)
    
    context['masse_mensuelle'] = masse_mensuelle
    context['mois'] = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 
                       'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc']
    
    return render(request, 'dashboard/statistiques_paie.html', context)
