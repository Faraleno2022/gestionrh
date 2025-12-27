"""
Vues pour l'interface de télédéclaration CNSS
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from datetime import date

from core.models import ConfigurationCNSS, TransmissionCNSS
from core.services.cnss import CNSSService
from core.views import log_activity


@login_required
def cnss_dashboard(request):
    """Tableau de bord CNSS"""
    entreprise = request.user.entreprise
    
    # Configuration
    try:
        config = ConfigurationCNSS.objects.get(entreprise=entreprise)
    except ConfigurationCNSS.DoesNotExist:
        config = None
    
    # Dernières transmissions
    transmissions = TransmissionCNSS.objects.filter(
        entreprise=entreprise
    ).order_by('-periode_annee', '-periode_mois')[:12]
    
    # Statistiques
    stats = {
        'total_transmissions': transmissions.count(),
        'transmis': transmissions.filter(statut='transmis').count(),
        'accepte': transmissions.filter(statut='accepte').count(),
        'en_attente': transmissions.filter(statut__in=['brouillon', 'genere']).count(),
    }
    
    return render(request, 'core/cnss/dashboard.html', {
        'config': config,
        'transmissions': transmissions,
        'stats': stats,
        'annee_courante': date.today().year,
        'mois_courant': date.today().month,
    })


@login_required
def cnss_configuration(request):
    """Configuration CNSS de l'entreprise"""
    entreprise = request.user.entreprise
    
    try:
        config = ConfigurationCNSS.objects.get(entreprise=entreprise)
    except ConfigurationCNSS.DoesNotExist:
        config = None
    
    if request.method == 'POST':
        if config:
            config.numero_employeur = request.POST.get('numero_employeur', '')
            config.code_agence = request.POST.get('code_agence', '')
            config.format_fichier = request.POST.get('format_fichier', 'csv')
            config.mode_declaration = request.POST.get('mode_declaration', 'manuel')
            config.save()
        else:
            config = ConfigurationCNSS.objects.create(
                entreprise=entreprise,
                numero_employeur=request.POST.get('numero_employeur', ''),
                code_agence=request.POST.get('code_agence', ''),
                format_fichier=request.POST.get('format_fichier', 'csv'),
                mode_declaration=request.POST.get('mode_declaration', 'manuel')
            )
        
        log_activity(request, "Configuration CNSS mise à jour", 'core')
        messages.success(request, 'Configuration CNSS enregistrée')
        return redirect('core:cnss_dashboard')
    
    return render(request, 'core/cnss/configuration.html', {
        'config': config,
    })


@login_required
def cnss_generer_declaration(request):
    """Générer une nouvelle déclaration CNSS"""
    entreprise = request.user.entreprise
    
    if request.method == 'POST':
        mois = int(request.POST.get('mois', date.today().month))
        annee = int(request.POST.get('annee', date.today().year))
        
        service = CNSSService(entreprise)
        transmission = service.generer_declaration(mois, annee)
        
        log_activity(
            request, 
            f"Génération déclaration CNSS {mois:02d}/{annee}",
            'core',
            'transmissions_cnss',
            transmission.id
        )
        
        messages.success(request, f'Déclaration CNSS {mois:02d}/{annee} générée')
        return redirect('core:cnss_detail', pk=transmission.id)
    
    # Liste des mois disponibles
    mois_disponibles = [
        (i, date(2000, i, 1).strftime('%B')) for i in range(1, 13)
    ]
    
    return render(request, 'core/cnss/generer.html', {
        'mois_disponibles': mois_disponibles,
        'mois_courant': date.today().month,
        'annee_courante': date.today().year,
    })


@login_required
def cnss_detail(request, pk):
    """Détail d'une transmission CNSS"""
    transmission = get_object_or_404(
        TransmissionCNSS, 
        pk=pk, 
        entreprise=request.user.entreprise
    )
    
    # Valider la déclaration
    service = CNSSService(request.user.entreprise)
    is_valid, errors = service.valider_declaration(transmission)
    
    return render(request, 'core/cnss/detail.html', {
        'transmission': transmission,
        'is_valid': is_valid,
        'errors': errors,
    })


@login_required
def cnss_telecharger(request, pk):
    """Télécharger le fichier de déclaration"""
    transmission = get_object_or_404(
        TransmissionCNSS, 
        pk=pk, 
        entreprise=request.user.entreprise
    )
    
    service = CNSSService(request.user.entreprise)
    contenu, extension = service.generer_fichier(transmission)
    
    # Mettre à jour le statut
    if transmission.statut == 'brouillon':
        transmission.statut = 'genere'
        transmission.save()
    
    # Préparer la réponse
    content_types = {
        'csv': 'text/csv',
        'xml': 'application/xml',
        'json': 'application/json',
    }
    
    filename = f"declaration_cnss_{transmission.periode_annee}{transmission.periode_mois:02d}.{extension}"
    
    response = HttpResponse(contenu, content_type=content_types.get(extension, 'text/plain'))
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    log_activity(
        request,
        f"Téléchargement déclaration CNSS {transmission.reference}",
        'core'
    )
    
    return response


@login_required
def cnss_marquer_transmis(request, pk):
    """Marquer une déclaration comme transmise"""
    transmission = get_object_or_404(
        TransmissionCNSS, 
        pk=pk, 
        entreprise=request.user.entreprise
    )
    
    if request.method == 'POST':
        transmission.statut = 'transmis'
        transmission.date_transmission = timezone.now()
        transmission.numero_accuse = request.POST.get('numero_accuse', '')
        transmission.save()
        
        log_activity(
            request,
            f"Déclaration CNSS {transmission.reference} marquée comme transmise",
            'core'
        )
        
        messages.success(request, 'Déclaration marquée comme transmise')
    
    return redirect('core:cnss_detail', pk=pk)


@login_required
def cnss_historique(request):
    """Historique des transmissions CNSS"""
    transmissions = TransmissionCNSS.objects.filter(
        entreprise=request.user.entreprise
    ).order_by('-periode_annee', '-periode_mois')
    
    # Filtres
    annee = request.GET.get('annee')
    if annee:
        transmissions = transmissions.filter(periode_annee=int(annee))
    
    statut = request.GET.get('statut')
    if statut:
        transmissions = transmissions.filter(statut=statut)
    
    # Années disponibles
    annees = TransmissionCNSS.objects.filter(
        entreprise=request.user.entreprise
    ).values_list('periode_annee', flat=True).distinct()
    
    return render(request, 'core/cnss/historique.html', {
        'transmissions': transmissions,
        'annees': sorted(set(annees), reverse=True),
        'annee_filtre': annee,
        'statut_filtre': statut,
    })
