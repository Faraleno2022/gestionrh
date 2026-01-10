from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from datetime import datetime, date
import json

from .models import (
    PeriodePaie, BulletinPaie, LigneBulletin, RubriquePaie,
    ElementSalaire, CumulPaie, HistoriquePaie, Constante, TrancheRTS,
    ParametrePaie, AlerteEcheance, ArchiveBulletin
)
from employes.models import Employe
from .services import MoteurCalculPaie
from core.decorators import reauth_required, entreprise_active_required


@login_required
@entreprise_active_required
@reauth_required
def paie_home(request):
    """Vue d'accueil du module paie"""
    # Statistiques générales
    periode_actuelle = PeriodePaie.objects.filter(
        entreprise=request.user.entreprise,
        statut_periode='ouverte'
    ).first()
    
    stats = {
        'periode_actuelle': periode_actuelle,
        'total_employes': Employe.objects.filter(
            entreprise=request.user.entreprise,
            statut_employe='actif'
        ).count(),
        'bulletins_mois': 0,
        'montant_total_brut': 0,
        'montant_total_net': 0,
    }
    
    if periode_actuelle:
        bulletins = BulletinPaie.objects.filter(
            periode=periode_actuelle,
            employe__entreprise=request.user.entreprise,
        )
        stats['bulletins_mois'] = bulletins.count()
        stats['montant_total_brut'] = bulletins.aggregate(Sum('salaire_brut'))['salaire_brut__sum'] or 0
        stats['montant_total_net'] = bulletins.aggregate(Sum('net_a_payer'))['net_a_payer__sum'] or 0
    
    return render(request, 'paie/home.html', {'stats': stats})


@login_required
@entreprise_active_required
@reauth_required
def liste_periodes(request):
    """Liste des périodes de paie"""
    periodes = PeriodePaie.objects.filter(
        entreprise=request.user.entreprise
    ).annotate(
        nb_bulletins=Count('bulletins')
    )
    
    return render(request, 'paie/periodes/liste.html', {
        'periodes': periodes
    })


@login_required
@entreprise_active_required
@reauth_required
def creer_periode(request):
    """Créer une nouvelle période de paie"""
    if request.method == 'POST':
        try:
            annee = int(request.POST.get('annee'))
            mois = int(request.POST.get('mois'))
            
            # Vérifier si la période existe déjà
            if PeriodePaie.objects.filter(
                entreprise=request.user.entreprise,
                annee=annee,
                mois=mois
            ).exists():
                messages.error(request, 'Cette période existe déjà.')
                return redirect('paie:liste_periodes')
            
            # Calculer les dates
            from calendar import monthrange
            nb_jours = monthrange(annee, mois)[1]
            date_debut = date(annee, mois, 1)
            date_fin = date(annee, mois, nb_jours)
            
            # Créer la période
            periode = PeriodePaie.objects.create(
                entreprise=request.user.entreprise,
                annee=annee,
                mois=mois,
                date_debut=date_debut,
                date_fin=date_fin,
                statut_periode='ouverte'
            )
            
            messages.success(request, f'Période {periode} créée avec succès.')
            return redirect('paie:detail_periode', pk=periode.pk)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création : {str(e)}')
    
    return render(request, 'paie/periodes/creer.html')


@login_required
@entreprise_active_required
@reauth_required
def detail_periode(request, pk):
    """Détail d'une période de paie"""
    periode = get_object_or_404(PeriodePaie, pk=pk, entreprise=request.user.entreprise)
    bulletins = BulletinPaie.objects.filter(
        periode=periode,
        employe__entreprise=request.user.entreprise,
    ).select_related('employe')
    
    # Statistiques de la période
    stats = bulletins.aggregate(
        total_brut=Sum('salaire_brut'),
        total_net=Sum('net_a_payer'),
        total_cnss_employe=Sum('cnss_employe'),
        total_cnss_employeur=Sum('cnss_employeur'),
        total_irg=Sum('irg')
    )
    
    return render(request, 'paie/periodes/detail.html', {
        'periode': periode,
        'bulletins': bulletins,
        'stats': stats
    })


@login_required
@entreprise_active_required
@reauth_required
def calculer_periode(request, pk):
    """Calculer tous les bulletins d'une période (OPTIMISÉ)"""
    periode = get_object_or_404(PeriodePaie, pk=pk, entreprise=request.user.entreprise)
    
    if periode.statut_periode not in ['ouverte', 'calculee']:
        messages.error(request, 'Cette période ne peut plus être calculée.')
        return redirect('paie:detail_periode', pk=pk)
    
    if request.method == 'POST':
        try:
            # Utiliser le service bulk optimisé
            from .services_bulk import BulkPayrollService
            
            bulk_service = BulkPayrollService(periode, request.user.entreprise)
            result = bulk_service.calculer_tous_bulletins(utilisateur=request.user)
            
            # Mettre à jour le statut de la période
            periode.statut_periode = 'calculee'
            periode.save()
            
            if result['erreurs']:
                messages.warning(
                    request,
                    f"{result['bulletins_crees']} bulletins créés en {result['temps_execution']}s. "
                    f"Erreurs: {', '.join(result['erreurs'][:5])}"
                    f"{'...' if len(result['erreurs']) > 5 else ''}"
                )
            else:
                messages.success(
                    request,
                    f"{result['bulletins_crees']} bulletins calculés en {result['temps_execution']}s."
                )
                
        except Exception as e:
            messages.error(request, f'Erreur lors du calcul : {str(e)}')
        
        return redirect('paie:detail_periode', pk=pk)
    
    # GET: Afficher la page de confirmation
    employes_count = Employe.objects.filter(
        entreprise=request.user.entreprise,
        statut_employe='actif'
    ).count()
    return render(request, 'paie/periodes/calculer.html', {
        'periode': periode,
        'employes_count': employes_count
    })


@login_required
@entreprise_active_required
@reauth_required
def valider_periode(request, pk):
    """Valider une période de paie"""
    periode = get_object_or_404(PeriodePaie, pk=pk, entreprise=request.user.entreprise)
    
    if periode.statut_periode != 'calculee':
        messages.error(request, 'La période doit être calculée avant validation.')
        return redirect('paie:detail_periode', pk=pk)
    
    if request.method == 'POST':
        with transaction.atomic():
            # Valider tous les bulletins
            BulletinPaie.objects.filter(
                periode=periode,
                employe__entreprise=request.user.entreprise,
            ).update(
                statut_bulletin='valide'
            )
            
            # Mettre à jour la période
            periode.statut_periode = 'validee'
            periode.save()
            
            # Archiver les bulletins pour traçabilité
            try:
                from .services_archive import ArchivageService
                stats = ArchivageService.archiver_periode(periode)
                if stats['archivés'] > 0:
                    messages.info(request, f"{stats['archivés']} bulletin(s) archivé(s) pour traçabilité.")
            except Exception as e:
                messages.warning(request, f"Archivage partiel: {e}")
            
            messages.success(request, 'Période validée avec succès.')
        
        return redirect('paie:detail_periode', pk=pk)
    
    return render(request, 'paie/periodes/valider.html', {'periode': periode})


@login_required
@entreprise_active_required
@reauth_required
def cloturer_periode(request, pk):
    """Clôturer une période de paie"""
    periode = get_object_or_404(PeriodePaie, pk=pk, entreprise=request.user.entreprise)
    
    if periode.statut_periode != 'validee':
        messages.error(request, 'La période doit être validée avant clôture.')
        return redirect('paie:detail_periode', pk=pk)
    
    if request.method == 'POST':
        with transaction.atomic():
            periode.statut_periode = 'cloturee'
            periode.date_cloture = timezone.now()
            periode.utilisateur_cloture = request.user
            periode.save()
            
            messages.success(request, 'Période clôturée avec succès.')
        
        return redirect('paie:detail_periode', pk=pk)
    
    return render(request, 'paie/periodes/cloturer.html', {'periode': periode})


@login_required
@entreprise_active_required
@reauth_required
def liste_bulletins(request):
    """Liste de tous les bulletins de paie (y compris périodes clôturées)"""
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    bulletins = BulletinPaie.objects.filter(
        employe__entreprise=request.user.entreprise,
        periode__entreprise=request.user.entreprise,
    ).select_related('employe', 'periode').order_by('-periode__annee', '-periode__mois', 'employe__nom')
    
    # Filtres
    annee = request.GET.get('annee')
    periode_id = request.GET.get('periode')
    employe_id = request.GET.get('employe')
    statut = request.GET.get('statut')
    
    if annee:
        bulletins = bulletins.filter(periode__annee=annee)
    if periode_id:
        bulletins = bulletins.filter(periode_id=periode_id)
    if employe_id:
        bulletins = bulletins.filter(employe_id=employe_id)
    if statut:
        bulletins = bulletins.filter(statut_bulletin=statut)
    
    # Pagination - 50 bulletins par page
    paginator = Paginator(bulletins, 50)
    page = request.GET.get('page')
    try:
        bulletins_page = paginator.page(page)
    except PageNotAnInteger:
        bulletins_page = paginator.page(1)
    except EmptyPage:
        bulletins_page = paginator.page(paginator.num_pages)
    
    # Toutes les périodes (y compris clôturées) pour le filtre
    periodes = PeriodePaie.objects.filter(
        entreprise=request.user.entreprise
    ).order_by('-annee', '-mois')
    
    # Tous les employés (actifs et inactifs) pour pouvoir consulter les anciens bulletins
    employes = Employe.objects.filter(
        entreprise=request.user.entreprise
    ).order_by('nom', 'prenoms')
    
    # Liste des années disponibles
    annees_disponibles = PeriodePaie.objects.filter(
        entreprise=request.user.entreprise
    ).values_list('annee', flat=True).distinct().order_by('-annee')
    
    return render(request, 'paie/bulletins/liste.html', {
        'bulletins': bulletins_page,
        'periodes': periodes,
        'employes': employes,
        'annees_disponibles': annees_disponibles,
        'annee_selectionnee': annee,
        'total_bulletins': paginator.count,
    })


@login_required
@entreprise_active_required
@reauth_required
def detail_bulletin(request, pk):
    """Détail d'un bulletin de paie"""
    bulletin = get_object_or_404(
        BulletinPaie,
        pk=pk,
        employe__entreprise=request.user.entreprise,
        periode__entreprise=request.user.entreprise,
    )
    lignes = LigneBulletin.objects.filter(bulletin=bulletin).select_related('rubrique')
    
    # Séparer les gains et retenues
    gains = lignes.filter(rubrique__type_rubrique='gain')
    retenues = lignes.filter(rubrique__type_rubrique__in=['retenue', 'cotisation'])
    
    return render(request, 'paie/bulletins/detail.html', {
        'bulletin': bulletin,
        'gains': gains,
        'retenues': retenues
    })


@login_required
@entreprise_active_required
@reauth_required
def imprimer_bulletin(request, pk):
    """Imprimer un bulletin de paie"""
    bulletin = get_object_or_404(
        BulletinPaie,
        pk=pk,
        employe__entreprise=request.user.entreprise,
        periode__entreprise=request.user.entreprise,
    )
    lignes = LigneBulletin.objects.filter(bulletin=bulletin).select_related('rubrique')
    
    # Récupérer les paramètres de l'entreprise
    try:
        params = ParametrePaie.objects.first()
    except:
        params = None
    
    gains = lignes.filter(rubrique__type_rubrique='gain')
    retenues = lignes.filter(rubrique__type_rubrique__in=['retenue', 'cotisation'])
    
    return render(request, 'paie/bulletins/imprimer.html', {
        'bulletin': bulletin,
        'gains': gains,
        'retenues': retenues,
        'params': params
    })


@login_required
@entreprise_active_required
def telecharger_bulletin_pdf(request, pk):
    """Télécharger un bulletin de paie en PDF avec ReportLab"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm, mm
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle
    import io
    import os
    
    bulletin = get_object_or_404(
        BulletinPaie,
        pk=pk,
        employe__entreprise=request.user.entreprise,
    )
    lignes = LigneBulletin.objects.filter(bulletin=bulletin).select_related('rubrique')
    gains = lignes.filter(rubrique__type_rubrique='gain')
    retenues = lignes.filter(rubrique__type_rubrique__in=['retenue', 'cotisation'])
    
    # Créer le buffer PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Variables de position
    y = height - 1*cm
    
    # === EN-TÊTE ===
    entreprise = bulletin.employe.entreprise
    
    # Logo entreprise à gauche
    if entreprise and entreprise.logo:
        try:
            logo_path = entreprise.logo.path
            if os.path.exists(logo_path):
                p.drawImage(logo_path, 1.5*cm, y - 2*cm, width=2*cm, height=2*cm, preserveAspectRatio=True)
        except:
            pass
    
    # Drapeau de la Guinée à droite (Rouge - Jaune - Vert)
    flag_width = 1.5*cm
    flag_height = 1*cm
    flag_x = width - 1.5*cm - flag_width
    flag_y = y - 1.5*cm
    stripe_width = flag_width / 3
    
    # Bande rouge
    p.setFillColor(colors.HexColor("#ce1126"))
    p.rect(flag_x, flag_y, stripe_width, flag_height, stroke=0, fill=1)
    # Bande jaune
    p.setFillColor(colors.HexColor("#fcd116"))
    p.rect(flag_x + stripe_width, flag_y, stripe_width, flag_height, stroke=0, fill=1)
    # Bande verte
    p.setFillColor(colors.HexColor("#009460"))
    p.rect(flag_x + 2*stripe_width, flag_y, stripe_width, flag_height, stroke=0, fill=1)
    # Bordure du drapeau
    p.setStrokeColor(colors.black)
    p.setLineWidth(0.5)
    p.rect(flag_x, flag_y, flag_width, flag_height, stroke=1, fill=0)
    p.setFillColor(colors.black)
    
    # Titre centré
    p.setFont("Helvetica-Bold", 11)
    p.drawCentredString(width/2, y, "RÉPUBLIQUE DE GUINÉE")
    y -= 0.4*cm
    p.setFont("Helvetica-Oblique", 8)
    p.drawCentredString(width/2, y, "Travail - Justice - Solidarité")
    y -= 0.5*cm
    
    # Nom entreprise
    p.setFont("Helvetica-Bold", 12)
    nom_entreprise = entreprise.nom_entreprise if entreprise else "ENTREPRISE"
    p.drawCentredString(width/2, y, nom_entreprise)
    y -= 0.6*cm
    
    # Titre bulletin
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width/2, y, "BULLETIN DE PAIE")
    y -= 0.4*cm
    
    # Ligne de séparation
    p.setStrokeColor(colors.HexColor("#ce1126"))
    p.setLineWidth(2)
    p.line(1.5*cm, y, width - 1.5*cm, y)
    y -= 0.6*cm
    
    # Infos bulletin sur une ligne
    p.setFont("Helvetica", 9)
    p.setFillColor(colors.black)
    p.drawString(1.5*cm, y, f"N°: {bulletin.numero_bulletin}")
    p.drawCentredString(width/2, y, f"Période: {bulletin.periode}")
    p.drawRightString(width - 1.5*cm, y, f"Date: {bulletin.date_calcul.strftime('%d/%m/%Y') if bulletin.date_calcul else '-'}")
    y -= 0.8*cm
    
    # === INFORMATIONS EMPLOYÉ ===
    p.setFillColor(colors.HexColor("#ce1126"))
    p.setFont("Helvetica-Bold", 9)
    p.drawString(1.5*cm, y, "INFORMATIONS EMPLOYÉ")
    p.setFillColor(colors.black)
    y -= 0.5*cm
    
    emp = bulletin.employe
    infos_emp = [
        ["Matricule:", emp.matricule or "-", "N° CNSS:", emp.num_cnss_individuel or "-"],
        ["Nom et Prénoms:", f"{emp.nom} {emp.prenoms}", "", ""],
        ["Poste:", str(emp.poste or "-"), "Service:", str(emp.service or "-")],
        ["Date embauche:", emp.date_embauche.strftime('%d/%m/%Y') if emp.date_embauche else "-", "Mode paiement:", emp.mode_paiement or "-"],
    ]
    
    for row in infos_emp:
        p.setFont("Helvetica-Bold", 8)
        p.drawString(1.5*cm, y, row[0])
        p.setFont("Helvetica", 8)
        p.drawString(4*cm, y, str(row[1]))
        if row[2]:
            p.setFont("Helvetica-Bold", 8)
            p.drawString(11*cm, y, row[2])
            p.setFont("Helvetica", 8)
            p.drawString(14*cm, y, str(row[3]))
        y -= 0.4*cm
    
    y -= 0.3*cm
    
    # === GAINS ===
    # Titre GAINS
    p.setFillColor(colors.HexColor("#28a745"))
    p.setFont("Helvetica-Bold", 9)
    p.drawString(1.5*cm, y, "GAINS ET RÉMUNÉRATIONS")
    p.setFillColor(colors.black)
    y -= 0.3*cm
    
    # Tableau des gains
    gains_data = [["Libellé", "Base", "Taux", "Montant"]]
    for g in gains:
        gains_data.append([
            g.rubrique.libelle_rubrique[:35],
            f"{g.base:,.0f}".replace(",", " ") if g.base else "-",
            f"{g.taux}%" if g.taux else "-",
            f"{g.montant:,.0f}".replace(",", " ")
        ])
    gains_data.append(["TOTAL BRUT", "", "", f"{bulletin.salaire_brut:,.0f} GNF".replace(",", " ")])
    
    row_height = 14
    gains_table = Table(gains_data, colWidths=[8*cm, 3*cm, 2*cm, 4*cm], rowHeights=row_height)
    gains_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#28a745")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#d4edda")),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    table_height = len(gains_data) * row_height
    gains_table.wrapOn(p, width, height)
    gains_table.drawOn(p, 1.5*cm, y - table_height)
    y -= table_height + 0.5*cm
    
    # === RETENUES ===
    # Titre RETENUES
    p.setFillColor(colors.HexColor("#dc3545"))
    p.setFont("Helvetica-Bold", 9)
    p.drawString(1.5*cm, y, "RETENUES ET COTISATIONS")
    p.setFillColor(colors.black)
    y -= 0.3*cm
    
    retenues_data = [["Libellé", "Base", "Taux", "Montant"]]
    for r in retenues:
        retenues_data.append([
            r.rubrique.libelle_rubrique[:35],
            f"{r.base:,.0f}".replace(",", " ") if r.base else "-",
            f"{r.taux}%" if r.taux else "-",
            f"{r.montant:,.0f}".replace(",", " ")
        ])
    
    # Ajouter CNSS et RTS
    retenues_data.append(["CNSS Employé (5%)", f"{bulletin.salaire_brut:,.0f}".replace(",", " "), "5%", f"{bulletin.cnss_employe:,.0f}".replace(",", " ")])
    retenues_data.append(["RTS (Impôt sur le Revenu)", "", "", f"{bulletin.irg:,.0f}".replace(",", " ")])
    
    retenues_table = Table(retenues_data, colWidths=[8*cm, 3*cm, 2*cm, 4*cm], rowHeights=row_height)
    retenues_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#dc3545")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    table_height = len(retenues_data) * row_height
    retenues_table.wrapOn(p, width, height)
    retenues_table.drawOn(p, 1.5*cm, y - table_height)
    y -= table_height + 0.6*cm
    
    # === RÉCAPITULATIF ===
    recap_height = 2.5*cm
    p.setStrokeColor(colors.HexColor("#ce1126"))
    p.setLineWidth(2)
    p.rect(1.5*cm, y - recap_height, width - 3*cm, recap_height, stroke=1, fill=0)
    
    p.setFont("Helvetica-Bold", 10)
    p.setFillColor(colors.black)
    p.drawString(2*cm, y - 0.5*cm, "SALAIRE BRUT:")
    p.drawRightString(width - 2*cm, y - 0.5*cm, f"{bulletin.salaire_brut:,.0f} GNF".replace(",", " "))
    
    p.setFont("Helvetica", 9)
    p.setFillColor(colors.HexColor("#dc3545"))
    p.drawString(2*cm, y - 1*cm, "Cotisation CNSS (5%):")
    p.drawRightString(width - 2*cm, y - 1*cm, f"- {bulletin.cnss_employe:,.0f} GNF".replace(",", " "))
    p.drawString(2*cm, y - 1.4*cm, "RTS:")
    p.drawRightString(width - 2*cm, y - 1.4*cm, f"- {bulletin.irg:,.0f} GNF".replace(",", " "))
    
    p.setFillColor(colors.HexColor("#28a745"))
    p.setFont("Helvetica-Bold", 11)
    p.drawString(2*cm, y - 2.1*cm, "NET À PAYER:")
    p.drawRightString(width - 2*cm, y - 2.1*cm, f"{bulletin.net_a_payer:,.0f} GNF".replace(",", " "))
    p.setFillColor(colors.black)
    
    y -= recap_height + 0.5*cm
    
    # === COTISATIONS PATRONALES ===
    p.setFont("Helvetica-Bold", 8)
    p.drawString(1.5*cm, y, "Cotisations patronales:")
    p.setFont("Helvetica", 8)
    p.drawString(5*cm, y, f"CNSS Employeur (18%): {bulletin.cnss_employeur:,.0f} GNF".replace(",", " "))
    total_cnss = bulletin.cnss_employe + bulletin.cnss_employeur
    p.drawString(11*cm, y, f"Total CNSS: {total_cnss:,.0f} GNF".replace(",", " "))
    
    # === PIED DE PAGE ===
    p.setFont("Helvetica", 7)
    p.drawCentredString(width/2, 2.2*cm, "Ce bulletin est conforme à la législation guinéenne en vigueur.")
    if entreprise:
        p.drawCentredString(width/2, 1.7*cm, f"{entreprise.nom_entreprise} - {entreprise.adresse or ''} - Tél: {entreprise.telephone or ''}")
        p.drawCentredString(width/2, 1.3*cm, f"NIF: {entreprise.nif or '-'} - CNSS: {entreprise.num_cnss or '-'}")
    
    p.drawCentredString(width/2, 0.8*cm, f"Document généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')}")
    
    # Finaliser le PDF
    p.showPage()
    p.save()
    
    # Retourner le PDF
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f"bulletin_{bulletin.numero_bulletin}_{emp.matricule}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def telecharger_bulletin_public(request, token):
    """Télécharger un bulletin de paie en PDF via lien public (sans authentification)"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm, mm
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle
    import io
    import os
    
    # Récupérer le bulletin par son token
    bulletin = get_object_or_404(BulletinPaie, token_public=token)
    
    lignes = LigneBulletin.objects.filter(bulletin=bulletin).select_related('rubrique')
    gains = lignes.filter(rubrique__type_rubrique='gain')
    retenues = lignes.filter(rubrique__type_rubrique__in=['retenue', 'cotisation'])
    
    # Créer le buffer PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Variables de position
    y = height - 1*cm
    
    # === EN-TÊTE ===
    entreprise = bulletin.employe.entreprise
    
    # Logo entreprise à gauche
    if entreprise and entreprise.logo:
        try:
            logo_path = entreprise.logo.path
            if os.path.exists(logo_path):
                p.drawImage(logo_path, 1.5*cm, y - 2*cm, width=2*cm, height=2*cm, preserveAspectRatio=True)
        except:
            pass
    
    # Drapeau de la Guinée à droite (Rouge - Jaune - Vert)
    flag_width = 1.5*cm
    flag_height = 1*cm
    flag_x = width - 1.5*cm - flag_width
    flag_y = y - 1.5*cm
    stripe_width = flag_width / 3
    
    # Bande rouge
    p.setFillColor(colors.HexColor("#ce1126"))
    p.rect(flag_x, flag_y, stripe_width, flag_height, stroke=0, fill=1)
    # Bande jaune
    p.setFillColor(colors.HexColor("#fcd116"))
    p.rect(flag_x + stripe_width, flag_y, stripe_width, flag_height, stroke=0, fill=1)
    # Bande verte
    p.setFillColor(colors.HexColor("#009460"))
    p.rect(flag_x + 2*stripe_width, flag_y, stripe_width, flag_height, stroke=0, fill=1)
    # Bordure du drapeau
    p.setStrokeColor(colors.black)
    p.setLineWidth(0.5)
    p.rect(flag_x, flag_y, flag_width, flag_height, stroke=1, fill=0)
    p.setFillColor(colors.black)
    
    # Titre centré
    p.setFont("Helvetica-Bold", 11)
    p.drawCentredString(width/2, y, "RÉPUBLIQUE DE GUINÉE")
    y -= 0.4*cm
    p.setFont("Helvetica-Oblique", 8)
    p.drawCentredString(width/2, y, "Travail - Justice - Solidarité")
    y -= 0.5*cm
    
    # Nom entreprise
    p.setFont("Helvetica-Bold", 12)
    nom_entreprise = entreprise.nom_entreprise if entreprise else "ENTREPRISE"
    p.drawCentredString(width/2, y, nom_entreprise)
    y -= 0.6*cm
    
    # Titre bulletin
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width/2, y, "BULLETIN DE PAIE")
    y -= 0.4*cm
    
    # Ligne de séparation
    p.setStrokeColor(colors.HexColor("#ce1126"))
    p.setLineWidth(2)
    p.line(1.5*cm, y, width - 1.5*cm, y)
    y -= 0.6*cm
    
    # Infos bulletin sur une ligne
    p.setFont("Helvetica", 9)
    p.setFillColor(colors.black)
    p.drawString(1.5*cm, y, f"N°: {bulletin.numero_bulletin}")
    p.drawCentredString(width/2, y, f"Période: {bulletin.periode}")
    p.drawRightString(width - 1.5*cm, y, f"Date: {bulletin.date_calcul.strftime('%d/%m/%Y') if bulletin.date_calcul else '-'}")
    y -= 0.8*cm
    
    # === INFORMATIONS EMPLOYÉ ===
    p.setFillColor(colors.HexColor("#ce1126"))
    p.setFont("Helvetica-Bold", 9)
    p.drawString(1.5*cm, y, "INFORMATIONS EMPLOYÉ")
    p.setFillColor(colors.black)
    y -= 0.5*cm
    
    emp = bulletin.employe
    infos_emp = [
        ["Matricule:", emp.matricule or "-", "N° CNSS:", emp.num_cnss_individuel or "-"],
        ["Nom et Prénoms:", f"{emp.nom} {emp.prenoms}", "", ""],
        ["Poste:", str(emp.poste or "-"), "Service:", str(emp.service or "-")],
        ["Date embauche:", emp.date_embauche.strftime('%d/%m/%Y') if emp.date_embauche else "-", "Mode paiement:", emp.mode_paiement or "-"],
    ]
    
    for row in infos_emp:
        p.setFont("Helvetica-Bold", 8)
        p.drawString(1.5*cm, y, row[0])
        p.setFont("Helvetica", 8)
        p.drawString(4*cm, y, str(row[1]))
        if row[2]:
            p.setFont("Helvetica-Bold", 8)
            p.drawString(11*cm, y, row[2])
            p.setFont("Helvetica", 8)
            p.drawString(14*cm, y, str(row[3]))
        y -= 0.4*cm
    
    y -= 0.3*cm
    
    # === GAINS ===
    p.setFillColor(colors.HexColor("#28a745"))
    p.setFont("Helvetica-Bold", 9)
    p.drawString(1.5*cm, y, "GAINS ET RÉMUNÉRATIONS")
    p.setFillColor(colors.black)
    y -= 0.3*cm
    
    # Tableau des gains
    gains_data = [["Libellé", "Base", "Taux", "Montant"]]
    for g in gains:
        gains_data.append([
            g.rubrique.libelle_rubrique[:35],
            f"{g.base:,.0f}".replace(",", " ") if g.base else "-",
            f"{g.taux}%" if g.taux else "-",
            f"{g.montant:,.0f}".replace(",", " ")
        ])
    gains_data.append(["TOTAL BRUT", "", "", f"{bulletin.salaire_brut:,.0f} GNF".replace(",", " ")])
    
    row_height = 14
    gains_table = Table(gains_data, colWidths=[8*cm, 3*cm, 2*cm, 4*cm], rowHeights=row_height)
    gains_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#28a745")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#d4edda")),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    table_height = len(gains_data) * row_height
    gains_table.wrapOn(p, width, height)
    gains_table.drawOn(p, 1.5*cm, y - table_height)
    y -= table_height + 0.5*cm
    
    # === RETENUES ===
    p.setFillColor(colors.HexColor("#dc3545"))
    p.setFont("Helvetica-Bold", 9)
    p.drawString(1.5*cm, y, "RETENUES ET COTISATIONS")
    p.setFillColor(colors.black)
    y -= 0.3*cm
    
    retenues_data = [["Libellé", "Base", "Taux", "Montant"]]
    for r in retenues:
        retenues_data.append([
            r.rubrique.libelle_rubrique[:35],
            f"{r.base:,.0f}".replace(",", " ") if r.base else "-",
            f"{r.taux}%" if r.taux else "-",
            f"{r.montant:,.0f}".replace(",", " ")
        ])
    
    # Ajouter CNSS et RTS
    retenues_data.append(["CNSS Employé (5%)", f"{bulletin.salaire_brut:,.0f}".replace(",", " "), "5%", f"{bulletin.cnss_employe:,.0f}".replace(",", " ")])
    retenues_data.append(["RTS (Impôt sur le Revenu)", "", "", f"{bulletin.irg:,.0f}".replace(",", " ")])
    
    retenues_table = Table(retenues_data, colWidths=[8*cm, 3*cm, 2*cm, 4*cm], rowHeights=row_height)
    retenues_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#dc3545")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    table_height = len(retenues_data) * row_height
    retenues_table.wrapOn(p, width, height)
    retenues_table.drawOn(p, 1.5*cm, y - table_height)
    y -= table_height + 0.6*cm
    
    # === RÉCAPITULATIF ===
    recap_height = 2.5*cm
    p.setStrokeColor(colors.HexColor("#ce1126"))
    p.setLineWidth(2)
    p.rect(1.5*cm, y - recap_height, width - 3*cm, recap_height, stroke=1, fill=0)
    
    p.setFont("Helvetica-Bold", 10)
    p.setFillColor(colors.black)
    p.drawString(2*cm, y - 0.5*cm, "SALAIRE BRUT:")
    p.drawRightString(width - 2*cm, y - 0.5*cm, f"{bulletin.salaire_brut:,.0f} GNF".replace(",", " "))
    
    p.setFont("Helvetica", 9)
    p.setFillColor(colors.HexColor("#dc3545"))
    p.drawString(2*cm, y - 1*cm, "Cotisation CNSS (5%):")
    p.drawRightString(width - 2*cm, y - 1*cm, f"- {bulletin.cnss_employe:,.0f} GNF".replace(",", " "))
    p.drawString(2*cm, y - 1.4*cm, "RTS:")
    p.drawRightString(width - 2*cm, y - 1.4*cm, f"- {bulletin.irg:,.0f} GNF".replace(",", " "))
    
    p.setFillColor(colors.HexColor("#28a745"))
    p.setFont("Helvetica-Bold", 11)
    p.drawString(2*cm, y - 2.1*cm, "NET À PAYER:")
    p.drawRightString(width - 2*cm, y - 2.1*cm, f"{bulletin.net_a_payer:,.0f} GNF".replace(",", " "))
    p.setFillColor(colors.black)
    
    y -= recap_height + 0.5*cm
    
    # === COTISATIONS PATRONALES ===
    p.setFont("Helvetica-Bold", 8)
    p.drawString(1.5*cm, y, "Cotisations patronales:")
    p.setFont("Helvetica", 8)
    p.drawString(5*cm, y, f"CNSS Employeur (18%): {bulletin.cnss_employeur:,.0f} GNF".replace(",", " "))
    total_cnss = bulletin.cnss_employe + bulletin.cnss_employeur
    p.drawString(11*cm, y, f"Total CNSS: {total_cnss:,.0f} GNF".replace(",", " "))
    
    # === PIED DE PAGE ===
    p.setFont("Helvetica", 7)
    p.drawCentredString(width/2, 2.2*cm, "Ce bulletin est conforme à la législation guinéenne en vigueur.")
    if entreprise:
        p.drawCentredString(width/2, 1.7*cm, f"{entreprise.nom_entreprise} - {entreprise.adresse or ''} - Tél: {entreprise.telephone or ''}")
        p.drawCentredString(width/2, 1.3*cm, f"NIF: {entreprise.nif or '-'} - CNSS: {entreprise.num_cnss or '-'}")
    
    p.drawCentredString(width/2, 0.8*cm, f"Document généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')}")
    
    # Finaliser le PDF
    p.showPage()
    p.save()
    
    # Retourner le PDF
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f"bulletin_{bulletin.numero_bulletin}_{emp.matricule}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def livre_paie(request):
    """Livre de paie conforme"""
    # Filtres
    annee = request.GET.get('annee', timezone.now().year)
    mois = request.GET.get('mois')
    
    periodes = PeriodePaie.objects.filter(
        entreprise=request.user.entreprise,
        annee=annee
    )
    if mois:
        periodes = periodes.filter(mois=mois)
    
    # Récupérer tous les bulletins des périodes avec total_retenues calculé
    from django.db.models import F
    bulletins = BulletinPaie.objects.filter(
        periode__in=periodes,
        employe__entreprise=request.user.entreprise,
    ).select_related('employe', 'employe__poste', 'periode').annotate(
        total_retenues=F('cnss_employe') + F('irg')
    ).order_by('periode__mois', 'employe__matricule')
    
    # Calcul des totaux
    totaux = bulletins.aggregate(
        total_brut=Sum('salaire_brut'),
        total_cnss_employe=Sum('cnss_employe'),
        total_cnss_employeur=Sum('cnss_employeur'),
        total_irg=Sum('irg'),
        total_net=Sum('net_a_payer'),
        total_retenues=Sum(F('cnss_employe') + F('irg'))
    )
    
    # Années disponibles
    annees = PeriodePaie.objects.filter(
        entreprise=request.user.entreprise
    ).values_list('annee', flat=True).distinct().order_by('-annee')
    
    return render(request, 'paie/livre_paie.html', {
        'bulletins': bulletins,
        'totaux': totaux,
        'annee': int(annee),
        'mois': int(mois) if mois else None,
        'annees': annees
    })


@login_required
@entreprise_active_required
def telecharger_livre_paie_pdf(request):
    """Télécharger le livre de paie en PDF"""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle
    from django.db.models import F
    import io

    annee = request.GET.get('annee', timezone.now().year)
    mois = request.GET.get('mois')

    periodes = PeriodePaie.objects.filter(
        entreprise=request.user.entreprise,
        annee=annee
    )
    if mois:
        periodes = periodes.filter(mois=mois)

    bulletins = BulletinPaie.objects.filter(
        periode__in=periodes,
        employe__entreprise=request.user.entreprise,
    ).select_related('employe', 'employe__poste', 'periode').annotate(
        total_retenues=F('cnss_employe') + F('irg')
    ).order_by('periode__mois', 'employe__matricule')

    totaux = bulletins.aggregate(
        total_brut=Sum('salaire_brut'),
        total_cnss_employe=Sum('cnss_employe'),
        total_cnss_employeur=Sum('cnss_employeur'),
        total_irg=Sum('irg'),
        total_net=Sum('net_a_payer'),
        total_retenues=Sum(F('cnss_employe') + F('irg'))
    )

    def fmt(val):
        try:
            n = float(val or 0)
        except Exception:
            n = 0
        return f"{n:,.0f}".replace(",", " ")

    buffer = io.BytesIO()
    page_size = landscape(A4)
    p = canvas.Canvas(buffer, pagesize=page_size)
    width, height = page_size

    y = height - 1.2 * cm
    p.setFont('Helvetica-Bold', 12)
    titre = f"Livre de Paie - Année {int(annee)}"
    if mois:
        titre += f" - Mois {int(mois)}"
    p.drawCentredString(width / 2, y, titre)
    y -= 0.6 * cm

    p.setStrokeColor(colors.HexColor('#0d6efd'))
    p.setLineWidth(2)
    p.line(1.2 * cm, y, width - 1.2 * cm, y)
    y -= 0.7 * cm

    p.setFont('Helvetica', 8)
    tot_line = (
        f"Brut: {fmt(totaux.get('total_brut'))} GNF   "
        f"CNSS Employé: {fmt(totaux.get('total_cnss_employe'))}   "
        f"CNSS Employeur: {fmt(totaux.get('total_cnss_employeur'))}   "
        f"RTS: {fmt(totaux.get('total_irg'))}   "
        f"Net: {fmt(totaux.get('total_net'))}"
    )
    p.drawString(1.2 * cm, y, tot_line)
    y -= 0.6 * cm

    data = [[
        'Période', 'Matr.', 'Nom et Prénoms', 'Fonction',
        'Brut', 'CNSS', 'RTS', 'Retenues', 'Net'
    ]]

    for b in bulletins:
        emp = b.employe
        nom_complet = f"{emp.nom} {emp.prenoms}"
        if len(nom_complet) > 25:
            nom_complet = nom_complet[:23] + '..'
        fonction = emp.poste.intitule_poste if emp.poste else '-'
        if len(fonction) > 18:
            fonction = fonction[:16] + '..'
        data.append([
            str(b.periode),
            emp.matricule or '-',
            nom_complet,
            fonction,
            fmt(b.salaire_brut),
            fmt(b.cnss_employe),
            fmt(b.irg),
            fmt(getattr(b, 'total_retenues', (b.cnss_employe or 0) + (b.irg or 0))),
            fmt(b.net_a_payer),
        ])

    data.append([
        'TOTAUX:', '', '', '',
        fmt(totaux.get('total_brut')),
        fmt(totaux.get('total_cnss_employe')),
        fmt(totaux.get('total_irg')),
        fmt(totaux.get('total_retenues')),
        fmt(totaux.get('total_net')),
    ])

    # Largeur disponible en A4 paysage: ~29.7cm - 2*0.8cm marges = ~28cm
    col_widths = [
        2.5 * cm, 2.0 * cm, 5.0 * cm, 3.5 * cm,
        3.0 * cm, 2.5 * cm, 2.5 * cm, 3.0 * cm, 3.0 * cm
    ]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 6),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 6),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9ecef')),
        ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (3, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 6),
        ('LINEABOVE', (0, -1), (-1, -1), 0.8, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))

    table_w, table_h = table.wrapOn(p, width - 2.4 * cm, y)
    table.drawOn(p, 1.2 * cm, max(1.2 * cm, y - table_h))

    p.showPage()
    p.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f"livre_paie_{int(annee)}"
    if mois:
        filename += f"_{int(mois)}"
    filename += ".pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def declarations_sociales(request):
    """Déclarations sociales (CNSS, RTS, INAM)"""
    # Filtres
    annee = request.GET.get('annee', timezone.now().year)
    mois = request.GET.get('mois')
    
    periodes = PeriodePaie.objects.filter(
        entreprise=request.user.entreprise,
        annee=annee
    )
    if mois:
        periodes = periodes.filter(mois=mois)
    
    # Inclure tous les bulletins calculés, validés ou payés
    bulletins = BulletinPaie.objects.filter(
        periode__in=periodes,
        statut_bulletin__in=['calcule', 'valide', 'paye'],
        employe__entreprise=request.user.entreprise,
    ).select_related('employe', 'periode')
    
    # Récupérer les constantes CNSS (plancher et plafond)
    from .models import Constante
    plancher_cnss = Constante.objects.filter(code='PLANCHER_CNSS', actif=True).first()
    plafond_cnss = Constante.objects.filter(code='PLAFOND_CNSS', actif=True).first()
    taux_cnss_employe = Constante.objects.filter(code='TAUX_CNSS_EMPLOYE', actif=True).first()
    taux_cnss_employeur = Constante.objects.filter(code='TAUX_CNSS_EMPLOYEUR', actif=True).first()
    
    # Calculs pour CNSS
    declaration_cnss = {
        'total_salaries': bulletins.values('employe').distinct().count(),
        'masse_salariale': bulletins.aggregate(Sum('salaire_brut'))['salaire_brut__sum'] or 0,
        'cotisation_employe': bulletins.aggregate(Sum('cnss_employe'))['cnss_employe__sum'] or 0,
        'cotisation_employeur': bulletins.aggregate(Sum('cnss_employeur'))['cnss_employeur__sum'] or 0,
        # Informations sur plancher et plafond
        'plancher': plancher_cnss.valeur if plancher_cnss else Decimal('550000'),
        'plafond': plafond_cnss.valeur if plafond_cnss else Decimal('2500000'),
        'taux_employe': taux_cnss_employe.valeur if taux_cnss_employe else Decimal('5.00'),
        'taux_employeur': taux_cnss_employeur.valeur if taux_cnss_employeur else Decimal('18.00'),
    }
    declaration_cnss['total_cotisation'] = (
        declaration_cnss['cotisation_employe'] + declaration_cnss['cotisation_employeur']
    )
    
    # Calculs pour RTS
    declaration_irg = {
        'total_salaries': bulletins.values('employe').distinct().count(),
        'masse_imposable': bulletins.aggregate(Sum('salaire_brut'))['salaire_brut__sum'] or 0,
        'total_irg': bulletins.aggregate(Sum('irg'))['irg__sum'] or 0,
    }
    
    # Calculs pour INAM (2.5% de la masse salariale)
    taux_inam = Decimal('2.5')
    declaration_inam = {
        'masse_salariale': declaration_cnss['masse_salariale'],
        'taux': taux_inam,
        'montant': (declaration_cnss['masse_salariale'] * taux_inam / Decimal('100')).quantize(Decimal('0.01'))
    }
    
    # Total général des charges
    total_general = (
        declaration_cnss['total_cotisation'] +
        declaration_irg['total_irg'] +
        declaration_inam['montant']
    )
    
    # Détail par employé
    detail_employes = []
    for bulletin in bulletins:
        detail_employes.append({
            'matricule': bulletin.employe.matricule,
            'nom_complet': f"{bulletin.employe.nom} {bulletin.employe.prenoms}",
            'periode': str(bulletin.periode),
            'brut': bulletin.salaire_brut,
            'cnss_employe': bulletin.cnss_employe,
            'cnss_employeur': bulletin.cnss_employeur,
            'irg': bulletin.irg,
            'net': bulletin.net_a_payer
        })
    
    annees = PeriodePaie.objects.filter(
        entreprise=request.user.entreprise
    ).values_list('annee', flat=True).distinct().order_by('-annee')
    
    return render(request, 'paie/declarations_sociales.html', {
        'declaration_cnss': declaration_cnss,
        'declaration_irg': declaration_irg,
        'declaration_inam': declaration_inam,
        'total_general': total_general,
        'detail_employes': detail_employes,
        'annee': int(annee),
        'mois': int(mois) if mois else None,
        'annees': annees,
        'periodes': periodes
    })


@login_required
def declarations_sociales_pdf(request):
    """Générer le PDF des déclarations sociales"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from io import BytesIO
    
    annee = request.GET.get('annee', timezone.now().year)
    mois = request.GET.get('mois')
    
    entreprise = request.user.entreprise
    if not entreprise:
        return HttpResponse("Aucune entreprise associée.", status=400)
    
    periodes = PeriodePaie.objects.filter(
        entreprise=entreprise,
        annee=annee,
        statut_periode__in=['validee', 'cloturee']
    )
    if mois:
        periodes = periodes.filter(mois=mois)
    
    bulletins = BulletinPaie.objects.filter(
        periode__in=periodes,
        statut_bulletin__in=['valide', 'paye'],
        employe__entreprise=entreprise,
    ).select_related('employe', 'periode')
    
    # Calculs
    declaration_cnss = {
        'total_salaries': bulletins.values('employe').distinct().count(),
        'masse_salariale': bulletins.aggregate(Sum('salaire_brut'))['salaire_brut__sum'] or 0,
        'cotisation_employe': bulletins.aggregate(Sum('cnss_employe'))['cnss_employe__sum'] or 0,
        'cotisation_employeur': bulletins.aggregate(Sum('cnss_employeur'))['cnss_employeur__sum'] or 0,
    }
    declaration_cnss['total_cotisation'] = declaration_cnss['cotisation_employe'] + declaration_cnss['cotisation_employeur']
    
    declaration_irg = {
        'total_salaries': bulletins.values('employe').distinct().count(),
        'total_irg': bulletins.aggregate(Sum('irg'))['irg__sum'] or 0,
    }
    
    # Créer le PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, alignment=1)
    periode_str = f"Mois {mois}/{annee}" if mois else f"Année {annee}"
    elements.append(Paragraph(f"Déclarations Sociales - {periode_str}", title_style))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(f"Entreprise: {entreprise.nom_entreprise}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))
    
    # CNSS
    elements.append(Paragraph("CNSS - Caisse Nationale de Sécurité Sociale", styles['Heading2']))
    cnss_data = [
        ['Libellé', 'Montant (GNF)'],
        ['Nombre de salariés', str(declaration_cnss['total_salaries'])],
        ['Masse salariale', f"{declaration_cnss['masse_salariale']:,.0f}"],
        ['Cotisation employé (5%)', f"{declaration_cnss['cotisation_employe']:,.0f}"],
        ['Cotisation employeur (18%)', f"{declaration_cnss['cotisation_employeur']:,.0f}"],
        ['Total cotisations', f"{declaration_cnss['total_cotisation']:,.0f}"],
    ]
    cnss_table = Table(cnss_data, colWidths=[10*cm, 6*cm])
    cnss_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EF7707')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f5f5f5')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(cnss_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # RTS/RTS
    elements.append(Paragraph("RTS/RTS - Retenue sur Traitements et Salaires", styles['Heading2']))
    irg_data = [
        ['Libellé', 'Montant (GNF)'],
        ['Nombre de salariés', str(declaration_irg['total_salaries'])],
        ['Total RTS retenu', f"{declaration_irg['total_irg']:,.0f}"],
    ]
    irg_table = Table(irg_data, colWidths=[10*cm, 6*cm])
    irg_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EF7707')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(irg_table)
    
    doc.build(elements)
    buffer.seek(0)
    
    filename = f"declarations_sociales_{annee}"
    if mois:
        filename += f"_{mois}"
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    return response


@login_required
def liste_elements_salaire(request):
    """Liste tous les éléments de salaire"""
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    # Filtres
    employe_id = request.GET.get('employe')
    type_rubrique = request.GET.get('type')
    actif = request.GET.get('actif')
    
    elements = ElementSalaire.objects.select_related(
        'employe', 'rubrique'
    ).filter(employe__entreprise=request.user.entreprise).order_by('employe__nom', 'rubrique__ordre_calcul')
    
    if employe_id:
        elements = elements.filter(employe_id=employe_id)
    if type_rubrique:
        elements = elements.filter(rubrique__type_rubrique=type_rubrique)
    if actif:
        elements = elements.filter(actif=(actif == 'true'))
    
    # Pagination - 50 par page
    paginator = Paginator(elements, 50)
    page = request.GET.get('page')
    try:
        elements_page = paginator.page(page)
    except PageNotAnInteger:
        elements_page = paginator.page(1)
    except EmptyPage:
        elements_page = paginator.page(paginator.num_pages)
    
    # Liste des employés pour le filtre
    employes = Employe.objects.filter(
        entreprise=request.user.entreprise,
        statut_employe='actif'
    ).order_by('nom', 'prenoms')
    
    return render(request, 'paie/elements_salaire/liste.html', {
        'elements': elements_page,
        'employes': employes,
        'total_elements': paginator.count,
    })


@login_required
def elements_salaire_employe(request, employe_id):
    """Éléments de salaire d'un employé spécifique"""
    employe = get_object_or_404(Employe, pk=employe_id, entreprise=request.user.entreprise)
    
    elements = ElementSalaire.objects.filter(
        employe=employe
    ).select_related('rubrique').order_by('rubrique__ordre_calcul')
    
    # Séparer gains et retenues
    gains = elements.filter(rubrique__type_rubrique='gain')
    retenues = elements.filter(rubrique__type_rubrique='retenue')
    
    # Calculer les totaux
    total_gains = sum(e.montant or 0 for e in gains if e.actif)
    total_retenues = sum(e.montant or 0 for e in retenues if e.actif)
    net_estime = total_gains - total_retenues
    
    return render(request, 'paie/elements_salaire/employe.html', {
        'employe': employe,
        'gains': gains,
        'retenues': retenues,
        'total_gains': total_gains,
        'total_retenues': total_retenues,
        'net_estime': net_estime
    })


@login_required
def ajouter_element_salaire(request, employe_id):
    """Ajouter un élément de salaire à un employé"""
    employe = get_object_or_404(Employe, pk=employe_id, entreprise=request.user.entreprise)
    
    if request.method == 'POST':
        rubrique_id = request.POST.get('rubrique')
        montant = request.POST.get('montant')
        taux = request.POST.get('taux')
        base_calcul = request.POST.get('base_calcul', '')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')
        actif = request.POST.get('actif') == 'on'
        recurrent = request.POST.get('recurrent') == 'on'
        
        try:
            rubrique = RubriquePaie.objects.get(pk=rubrique_id)
            
            # Vérifier si un élément actif existe déjà pour cette rubrique
            element_existant = ElementSalaire.objects.filter(
                employe=employe,
                rubrique=rubrique,
                actif=True
            ).first()
            
            if element_existant:
                messages.error(
                    request,
                    f'Un élément "{rubrique.libelle_rubrique}" actif existe déjà pour {employe.nom_complet}. '
                    f'Veuillez le modifier ou le désactiver avant d\'en ajouter un nouveau.'
                )
                return redirect('paie:elements_salaire_employe', employe_id=employe.id)
            
            element = ElementSalaire.objects.create(
                employe=employe,
                rubrique=rubrique,
                montant=Decimal(montant) if montant else None,
                taux=Decimal(taux) if taux else None,
                base_calcul=base_calcul,
                date_debut=date_debut,
                date_fin=date_fin if date_fin else None,
                actif=actif,
                recurrent=recurrent
            )
            
            messages.success(
                request,
                f'Élément "{rubrique.libelle_rubrique}" ajouté avec succès pour {employe.nom_complet}'
            )
            return redirect('paie:elements_salaire_employe', employe_id=employe.id)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ajout : {str(e)}')
    
    # Rubriques disponibles (exclure celles calculées automatiquement: IRG, CNSS)
    rubriques = RubriquePaie.objects.filter(
        actif=True
    ).exclude(
        code_rubrique__in=['RTS', 'IRG', 'IRPP', 'CNSS_EMP', 'CNSS_PAT']
    ).exclude(
        code_rubrique__icontains='CNSS'
    ).exclude(
        libelle_rubrique__icontains='Impôt sur le Revenu'
    ).order_by('type_rubrique', 'libelle_rubrique')
    
    return render(request, 'paie/elements_salaire/ajouter.html', {
        'employe': employe,
        'rubriques': rubriques
    })


@login_required
def modifier_element_salaire(request, pk):
    """Modifier un élément de salaire"""
    element = get_object_or_404(ElementSalaire, pk=pk, employe__entreprise=request.user.entreprise)
    
    if request.method == 'POST':
        montant = request.POST.get('montant')
        taux = request.POST.get('taux')
        base_calcul = request.POST.get('base_calcul', '')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')
        actif = request.POST.get('actif') == 'on'
        recurrent = request.POST.get('recurrent') == 'on'
        
        try:
            element.montant = Decimal(montant) if montant else None
            element.taux = Decimal(taux) if taux else None
            element.base_calcul = base_calcul
            element.date_debut = date_debut
            element.date_fin = date_fin if date_fin else None
            element.actif = actif
            element.recurrent = recurrent
            element.save()
            
            messages.success(request, 'Élément modifié avec succès')
            return redirect('paie:elements_salaire_employe', employe_id=element.employe.id)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification : {str(e)}')
    
    return render(request, 'paie/elements_salaire/modifier.html', {
        'element': element
    })


@login_required
def supprimer_element_salaire(request, pk):
    """Supprimer un élément de salaire"""
    element = get_object_or_404(ElementSalaire, pk=pk, employe__entreprise=request.user.entreprise)
    employe_id = element.employe.id
    
    if request.method == 'POST':
        libelle = element.rubrique.libelle_rubrique
        element.delete()
        messages.success(request, f'Élément "{libelle}" supprimé avec succès')
        return redirect('paie:elements_salaire_employe', employe_id=employe_id)
    
    return render(request, 'paie/elements_salaire/supprimer.html', {
        'element': element
    })


@login_required
def liste_rubriques(request):
    """Liste des rubriques de paie"""
    type_rubrique = request.GET.get('type')
    
    rubriques = RubriquePaie.objects.all()
    
    if type_rubrique:
        rubriques = rubriques.filter(type_rubrique=type_rubrique)
    
    # Statistiques
    stats = {
        'total': rubriques.count(),
        'gains': rubriques.filter(type_rubrique='gain').count(),
        'retenues': rubriques.filter(type_rubrique='retenue').count(),
        'cotisations': rubriques.filter(type_rubrique='cotisation').count(),
    }
    
    return render(request, 'paie/rubriques/liste.html', {
        'rubriques': rubriques,
        'stats': stats
    })


@login_required
def creer_rubrique(request):
    """Créer une nouvelle rubrique de paie"""
    if request.method == 'POST':
        code = request.POST.get('code_rubrique')
        libelle = request.POST.get('libelle_rubrique')
        type_rub = request.POST.get('type_rubrique')
        formule = request.POST.get('formule_calcul', '')
        taux = request.POST.get('taux_rubrique')
        montant_fixe = request.POST.get('montant_fixe')
        soumis_cnss = request.POST.get('soumis_cnss') == 'on'
        soumis_irg = request.POST.get('soumis_irg') == 'on'
        ordre_calcul = request.POST.get('ordre_calcul', 100)
        ordre_affichage = request.POST.get('ordre_affichage', 100)
        affichage_bulletin = request.POST.get('affichage_bulletin') == 'on'
        actif = request.POST.get('actif') == 'on'
        
        try:
            rubrique = RubriquePaie.objects.create(
                code_rubrique=code,
                libelle_rubrique=libelle,
                type_rubrique=type_rub,
                formule_calcul=formule,
                taux_rubrique=Decimal(taux) if taux else None,
                montant_fixe=Decimal(montant_fixe) if montant_fixe else None,
                soumis_cnss=soumis_cnss,
                soumis_irg=soumis_irg,
                ordre_calcul=int(ordre_calcul),
                ordre_affichage=int(ordre_affichage),
                affichage_bulletin=affichage_bulletin,
                actif=actif
            )
            
            messages.success(request, f'Rubrique "{libelle}" créée avec succès')
            return redirect('paie:liste_rubriques')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création : {str(e)}')
    
    return render(request, 'paie/rubriques/creer.html')


@login_required
def detail_rubrique(request, pk):
    """Détail d'une rubrique de paie"""
    rubrique = get_object_or_404(RubriquePaie, pk=pk)
    
    # Nombre d'employés utilisant cette rubrique
    nb_employes = ElementSalaire.objects.filter(
        rubrique=rubrique,
        actif=True,
        employe__entreprise=request.user.entreprise,
    ).values('employe').distinct().count()
    
    # Éléments utilisant cette rubrique
    elements = ElementSalaire.objects.filter(
        rubrique=rubrique,
        employe__entreprise=request.user.entreprise,
    ).select_related('employe').order_by('-actif', 'employe__nom')[:20]
    
    return render(request, 'paie/rubriques/detail.html', {
        'rubrique': rubrique,
        'nb_employes': nb_employes,
        'elements': elements
    })


@login_required
@entreprise_active_required
def tableau_bord_echeances(request):
    """Tableau de bord des échéances de déclarations sociales"""
    aujourd_hui = date.today()
    entreprise = request.user.entreprise
    
    # Générer/actualiser les alertes pour le mois en cours
    mois_courant = aujourd_hui.month
    annee_courante = aujourd_hui.year
    
    # Mois précédent (pour les déclarations en cours)
    if mois_courant == 1:
        mois_declaration = 12
        annee_declaration = annee_courante - 1
    else:
        mois_declaration = mois_courant - 1
        annee_declaration = annee_courante
    
    # Générer les alertes si elles n'existent pas
    AlerteEcheance.generer_alertes_mois(entreprise, annee_declaration, mois_declaration)
    
    # Actualiser toutes les alertes
    alertes = AlerteEcheance.objects.filter(
        entreprise=entreprise,
        statut__in=['a_venir', 'urgent', 'en_retard']
    )
    for alerte in alertes:
        alerte.actualiser_statut()
    
    # Récupérer les alertes triées
    alertes_urgentes = AlerteEcheance.objects.filter(
        entreprise=entreprise,
        statut__in=['urgent', 'en_retard']
    ).order_by('date_echeance')
    
    alertes_a_venir = AlerteEcheance.objects.filter(
        entreprise=entreprise,
        statut='a_venir'
    ).order_by('date_echeance')[:10]
    
    alertes_traitees = AlerteEcheance.objects.filter(
        entreprise=entreprise,
        statut='traite'
    ).order_by('-date_echeance')[:5]
    
    # Statistiques
    stats = {
        'total_urgentes': alertes_urgentes.count(),
        'total_a_venir': alertes_a_venir.count(),
        'total_en_retard': AlerteEcheance.objects.filter(
            entreprise=entreprise,
            statut='en_retard'
        ).count(),
    }
    
    # Prochaine échéance
    prochaine_echeance = AlerteEcheance.objects.filter(
        entreprise=entreprise,
        statut__in=['a_venir', 'urgent']
    ).order_by('date_echeance').first()
    
    return render(request, 'paie/echeances/tableau_bord.html', {
        'alertes_urgentes': alertes_urgentes,
        'alertes_a_venir': alertes_a_venir,
        'alertes_traitees': alertes_traitees,
        'stats': stats,
        'prochaine_echeance': prochaine_echeance,
        'aujourd_hui': aujourd_hui,
    })


@login_required
@entreprise_active_required
def marquer_alerte_traitee(request, pk):
    """Marque une alerte comme traitée"""
    alerte = get_object_or_404(AlerteEcheance, pk=pk, entreprise=request.user.entreprise)
    
    alerte.statut = 'traite'
    alerte.lu = True
    alerte.date_lecture = timezone.now()
    alerte.save()
    
    messages.success(request, f'Alerte "{alerte.get_type_echeance_display()}" marquée comme traitée.')
    return redirect('paie:tableau_bord_echeances')


@login_required
@entreprise_active_required
def api_alertes_echeances(request):
    """API pour récupérer les alertes (pour le header/notifications)"""
    entreprise = request.user.entreprise
    
    # Actualiser et récupérer les alertes urgentes
    alertes = AlerteEcheance.objects.filter(
        entreprise=entreprise,
        statut__in=['urgent', 'en_retard'],
        lu=False
    ).order_by('date_echeance')[:5]
    
    data = {
        'count': alertes.count(),
        'alertes': [
            {
                'id': a.id,
                'type': a.get_type_echeance_display(),
                'message': a.message,
                'niveau': a.niveau_alerte,
                'jours_restants': a.jours_restants,
                'date_echeance': a.date_echeance.strftime('%d/%m/%Y'),
            }
            for a in alertes
        ]
    }
    
    return JsonResponse(data)


@login_required
@entreprise_active_required
def historique_bulletins(request):
    """Historique des bulletins de paie avec recherche"""
    entreprise = request.user.entreprise
    
    # Filtres
    annee = request.GET.get('annee', date.today().year)
    mois = request.GET.get('mois', '')
    employe_id = request.GET.get('employe', '')
    recherche = request.GET.get('q', '')
    
    # Base query
    bulletins = BulletinPaie.objects.filter(
        employe__entreprise=entreprise,
        statut_bulletin__in=['valide', 'paye']
    ).select_related('employe', 'periode')
    
    # Appliquer les filtres
    if annee:
        bulletins = bulletins.filter(periode__annee=int(annee))
    if mois:
        bulletins = bulletins.filter(periode__mois=int(mois))
    if employe_id:
        bulletins = bulletins.filter(employe_id=employe_id)
    if recherche:
        bulletins = bulletins.filter(
            Q(employe__nom__icontains=recherche) |
            Q(employe__prenoms__icontains=recherche) |
            Q(employe__matricule__icontains=recherche) |
            Q(numero_bulletin__icontains=recherche)
        )
    
    bulletins = bulletins.order_by('-periode__annee', '-periode__mois', 'employe__nom')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(bulletins, 25)
    page = request.GET.get('page', 1)
    bulletins_page = paginator.get_page(page)
    
    # Statistiques
    stats = {
        'total_bulletins': bulletins.count(),
        'total_brut': bulletins.aggregate(Sum('salaire_brut'))['salaire_brut__sum'] or 0,
        'total_net': bulletins.aggregate(Sum('net_a_payer'))['net_a_payer__sum'] or 0,
    }
    
    # Listes pour les filtres
    annees = PeriodePaie.objects.filter(
        entreprise=entreprise
    ).values_list('annee', flat=True).distinct().order_by('-annee')
    
    employes = Employe.objects.filter(
        entreprise=entreprise,
        statut_employe='actif'
    ).order_by('nom', 'prenoms')
    
    return render(request, 'paie/historique_bulletins.html', {
        'bulletins': bulletins_page,
        'stats': stats,
        'annees': annees,
        'employes': employes,
        'annee_selectionnee': int(annee) if annee else None,
        'mois_selectionne': int(mois) if mois else None,
        'employe_selectionne': int(employe_id) if employe_id else None,
        'recherche': recherche,
    })


@login_required
@entreprise_active_required
def telecharger_bulletins_masse(request):
    """Télécharge plusieurs bulletins en ZIP"""
    import zipfile
    import io
    
    entreprise = request.user.entreprise
    annee = request.GET.get('annee')
    mois = request.GET.get('mois')
    
    if not annee or not mois:
        messages.error(request, "Veuillez sélectionner une année et un mois")
        return redirect('paie:historique_bulletins')
    
    bulletins = BulletinPaie.objects.filter(
        employe__entreprise=entreprise,
        periode__annee=int(annee),
        periode__mois=int(mois),
        statut_bulletin__in=['valide', 'paye']
    ).select_related('employe', 'periode')
    
    if not bulletins.exists():
        messages.warning(request, "Aucun bulletin trouvé pour cette période")
        return redirect('paie:historique_bulletins')
    
    # Créer le ZIP en mémoire
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for bulletin in bulletins:
            # Générer le PDF du bulletin
            from .utils import generer_bulletin_pdf
            try:
                pdf_content = generer_bulletin_pdf(bulletin)
                filename = f"Bulletin_{bulletin.employe.matricule}_{annee}_{mois:02d}.pdf"
                zip_file.writestr(filename, pdf_content)
            except Exception as e:
                continue
    
    buffer.seek(0)
    
    response = HttpResponse(buffer.read(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="Bulletins_{annee}_{mois:02d}.zip"'
    return response


@login_required
@entreprise_active_required
def attestation_salaire(request, employe_id):
    """Génère une attestation de salaire pour un employé"""
    employe = get_object_or_404(Employe, pk=employe_id, entreprise=request.user.entreprise)
    
    # Récupérer les 12 derniers bulletins
    bulletins = BulletinPaie.objects.filter(
        employe=employe,
        statut_bulletin__in=['valide', 'paye']
    ).order_by('-periode__annee', '-periode__mois')[:12]
    
    if not bulletins:
        messages.warning(request, "Aucun bulletin trouvé pour cet employé")
        return redirect('paie:historique_bulletins')
    
    # Calculer les moyennes
    from django.db.models import Avg
    stats = bulletins.aggregate(
        salaire_moyen=Avg('salaire_brut'),
        net_moyen=Avg('net_a_payer'),
    )
    
    dernier_bulletin = bulletins.first()
    
    context = {
        'employe': employe,
        'bulletins': bulletins,
        'stats': stats,
        'dernier_bulletin': dernier_bulletin,
        'date_attestation': date.today(),
        'entreprise': request.user.entreprise,
    }
    
    return render(request, 'paie/attestation_salaire.html', context)


@login_required
@entreprise_active_required
def simulation_paie(request):
    """Simulateur de paie - Calcul sans enregistrement"""
    entreprise = request.user.entreprise
    resultat = None
    employe_selectionne = None
    
    # Liste des employés actifs
    employes = Employe.objects.filter(
        entreprise=entreprise,
        statut_employe='actif'
    ).order_by('nom', 'prenoms')
    
    if request.method == 'POST':
        employe_id = request.POST.get('employe')
        salaire_base = request.POST.get('salaire_base', '0')
        
        # Récupérer les primes/indemnités du formulaire
        prime_transport = request.POST.get('prime_transport', '0')
        prime_logement = request.POST.get('prime_logement', '0')
        prime_panier = request.POST.get('prime_panier', '0')
        prime_anciennete = request.POST.get('prime_anciennete', '0')
        prime_responsabilite = request.POST.get('prime_responsabilite', '0')
        autres_primes = request.POST.get('autres_primes', '0')
        
        # Convertir en Decimal
        try:
            salaire_base = Decimal(salaire_base.replace(' ', '').replace(',', '.'))
            prime_transport = Decimal(prime_transport.replace(' ', '').replace(',', '.') or '0')
            prime_logement = Decimal(prime_logement.replace(' ', '').replace(',', '.') or '0')
            prime_panier = Decimal(prime_panier.replace(' ', '').replace(',', '.') or '0')
            prime_anciennete = Decimal(prime_anciennete.replace(' ', '').replace(',', '.') or '0')
            prime_responsabilite = Decimal(prime_responsabilite.replace(' ', '').replace(',', '.') or '0')
            autres_primes = Decimal(autres_primes.replace(' ', '').replace(',', '.') or '0')
        except:
            messages.error(request, "Erreur dans les montants saisis")
            return redirect('paie:simulation_paie')
        
        # Calculer le brut
        salaire_brut = (salaire_base + prime_transport + prime_logement + 
                       prime_panier + prime_anciennete + prime_responsabilite + autres_primes)
        
        # Récupérer les constantes
        plancher_cnss = Decimal('550000')
        plafond_cnss = Decimal('2500000')
        taux_cnss_employe = Decimal('5')
        taux_cnss_employeur = Decimal('18')
        taux_vf = Decimal('6')
        taux_ta = Decimal('1.5')
        
        try:
            const = Constante.objects.filter(code='PLANCHER_CNSS', actif=True).first()
            if const: plancher_cnss = const.valeur
            const = Constante.objects.filter(code='PLAFOND_CNSS', actif=True).first()
            if const: plafond_cnss = const.valeur
        except:
            pass
        
        # Calcul CNSS avec vérification du seuil minimum
        # Si salaire brut < 10% du plancher (55 000 GNF), pas de cotisation CNSS
        seuil_minimum_cnss = plancher_cnss * Decimal('0.10')
        alertes = []
        
        if salaire_brut <= 0:
            assiette_cnss = Decimal('0')
            cnss_employe = Decimal('0')
            cnss_employeur = Decimal('0')
            alertes.append({
                'type': 'critique',
                'message': f"Salaire brut nul ou négatif ({salaire_brut:,.0f} GNF). Vérifiez les éléments de salaire."
            })
        elif salaire_brut < seuil_minimum_cnss:
            assiette_cnss = Decimal('0')
            cnss_employe = Decimal('0')
            cnss_employeur = Decimal('0')
            alertes.append({
                'type': 'avertissement',
                'message': f"Salaire brut très faible ({salaire_brut:,.0f} GNF < {seuil_minimum_cnss:,.0f} GNF). Pas de cotisation CNSS calculée."
            })
        else:
            assiette_cnss = min(max(salaire_brut, plancher_cnss), plafond_cnss)
            cnss_employe = (assiette_cnss * taux_cnss_employe / Decimal('100')).quantize(Decimal('1'))
            cnss_employeur = (assiette_cnss * taux_cnss_employeur / Decimal('100')).quantize(Decimal('1'))
        
        # Vérifier plafond 25% indemnités forfaitaires
        # FORMULE CORRECTE:
        # Salaire brut = Salaire de base + Primes/Indemnités
        # Plafond exonéré = 25% × Salaire brut
        # Si Primes > Plafond → Excédent réintégré dans base RTS
        #
        # VÉRIFICATION MATHÉMATIQUE:
        # Pour que les primes soient exactement au plafond:
        # Primes = 25% × (Salaire de base + Primes)
        # Primes = 0.25 × Salaire de base + 0.25 × Primes
        # 0.75 × Primes = 0.25 × Salaire de base
        # Primes = 33.33% × Salaire de base
        # → Pour respecter le plafond 25% du brut, les primes ne doivent pas dépasser ~33% du salaire de base.
        
        total_indemnites_forfaitaires = prime_transport + prime_logement + prime_panier
        # Plafond = 25% du salaire brut (salaire de base + indemnités)
        plafond_indemnites = (salaire_brut * Decimal('0.25')).quantize(Decimal('1'))
        exces_indemnites = max(Decimal('0'), total_indemnites_forfaitaires - plafond_indemnites)
        
        # Calcul du seuil théorique: primes max = 33.33% du salaire de base
        primes_max_theorique = (salaire_base * Decimal('0.3333')).quantize(Decimal('1'))
        
        # Alerte si dépassement du plafond
        if exces_indemnites > 0:
            alertes.append({
                'type': 'avertissement',
                'message': f"Plafond 25% indemnités forfaitaires dépassé: {total_indemnites_forfaitaires:,.0f} GNF > {plafond_indemnites:,.0f} GNF. "
                           f"Excédent {exces_indemnites:,.0f} GNF réintégré dans base RTS."
            })
        
        # Base imposable RTS = Brut - CNSS + Excédent indemnités
        base_imposable = salaire_brut - cnss_employe + exces_indemnites
        
        # Calcul RTS par tranches (CGI 2022 - 6 tranches)
        tranches_rts = [
            (Decimal('0'), Decimal('1000000'), Decimal('0')),
            (Decimal('1000001'), Decimal('3000000'), Decimal('5')),
            (Decimal('3000001'), Decimal('5000000'), Decimal('8')),
            (Decimal('5000001'), Decimal('10000000'), Decimal('10')),
            (Decimal('10000001'), Decimal('20000000'), Decimal('15')),
            (Decimal('20000001'), None, Decimal('20')),
        ]
        
        rts = Decimal('0')
        detail_rts = []
        reste = base_imposable
        
        for borne_inf, borne_sup, taux in tranches_rts:
            if reste <= 0:
                break
            if borne_sup:
                montant_tranche = min(reste, borne_sup - borne_inf + 1)
            else:
                montant_tranche = reste
            
            if base_imposable >= borne_inf:
                impot_tranche = (montant_tranche * taux / Decimal('100')).quantize(Decimal('1'))
                rts += impot_tranche
                if montant_tranche > 0:
                    detail_rts.append({
                        'borne_inf': borne_inf,
                        'borne_sup': borne_sup,
                        'taux': taux,
                        'montant': montant_tranche,
                        'impot': impot_tranche,
                    })
                reste -= montant_tranche
        
        # Charges patronales
        vf = (salaire_brut * taux_vf / Decimal('100')).quantize(Decimal('1'))
        ta = (salaire_brut * taux_ta / Decimal('100')).quantize(Decimal('1'))
        
        # Totaux
        total_retenues = cnss_employe + rts
        net_a_payer = salaire_brut - total_retenues
        total_charges_patronales = cnss_employeur + vf + ta
        cout_total_employeur = salaire_brut + total_charges_patronales
        retenues_excessives = Decimal('0')
        
        # Protection: Empêcher le net négatif
        if net_a_payer < 0:
            alertes.append({
                'type': 'critique',
                'message': f"Net à payer serait négatif ({net_a_payer:,.0f} GNF). Les retenues ({total_retenues:,.0f} GNF) dépassent le brut ({salaire_brut:,.0f} GNF). Retenues plafonnées."
            })
            retenues_excessives = abs(net_a_payer)
            total_retenues = salaire_brut
            net_a_payer = Decimal('0')
        
        # Employé sélectionné
        if employe_id:
            employe_selectionne = Employe.objects.filter(pk=employe_id).first()
        
        resultat = {
            'salaire_base': salaire_base,
            'prime_transport': prime_transport,
            'prime_logement': prime_logement,
            'prime_panier': prime_panier,
            'prime_anciennete': prime_anciennete,
            'prime_responsabilite': prime_responsabilite,
            'autres_primes': autres_primes,
            'salaire_brut': salaire_brut,
            'assiette_cnss': assiette_cnss,
            'cnss_employe': cnss_employe,
            'cnss_employeur': cnss_employeur,
            # Plafond 25% indemnités forfaitaires
            'total_indemnites_forfaitaires': total_indemnites_forfaitaires,
            'plafond_indemnites': plafond_indemnites,
            'exces_indemnites': exces_indemnites,
            'primes_max_theorique': primes_max_theorique,  # 33.33% du salaire de base
            'base_imposable': base_imposable,
            'rts': rts,
            'detail_rts': detail_rts,
            'vf': vf,
            'ta': ta,
            'total_retenues': total_retenues,
            'net_a_payer': net_a_payer,
            'total_charges_patronales': total_charges_patronales,
            'cout_total_employeur': cout_total_employeur,
            'taux_cnss_employe': taux_cnss_employe,
            'taux_cnss_employeur': taux_cnss_employeur,
            'taux_vf': taux_vf,
            'taux_ta': taux_ta,
            'alertes': alertes,
            'seuil_minimum_cnss': seuil_minimum_cnss,
            'retenues_excessives': retenues_excessives,
        }
    
    return render(request, 'paie/simulation_paie.html', {
        'employes': employes,
        'resultat': resultat,
        'employe_selectionne': employe_selectionne,
    })


# ============================================
# VUES ARCHIVES BULLETINS - TRAÇABILITÉ
# ============================================

@login_required
@entreprise_active_required
def liste_archives(request):
    """Liste des bulletins archivés avec statistiques"""
    from .services_archive import ArchivageService
    
    entreprise = request.user.entreprise
    
    archives = ArchiveBulletin.objects.filter(
        bulletin__employe__entreprise=entreprise
    ).select_related('bulletin', 'bulletin__employe').order_by(
        '-periode_annee', '-periode_mois', 'employe_nom'
    )
    
    # Filtres
    annee = request.GET.get('annee')
    if annee:
        archives = archives.filter(periode_annee=int(annee))
    
    mois = request.GET.get('mois')
    if mois:
        archives = archives.filter(periode_mois=int(mois))
    
    # Stats
    stats = ArchivageService.stats_archives(entreprise)
    
    # Années disponibles
    annees = ArchiveBulletin.objects.filter(
        bulletin__employe__entreprise=entreprise
    ).values_list('periode_annee', flat=True).distinct().order_by('-periode_annee')
    
    return render(request, 'paie/archives/liste.html', {
        'archives': archives[:100],
        'stats': stats,
        'annees': annees,
        'annee_filtre': annee,
        'mois_filtre': mois,
    })


@login_required
@entreprise_active_required
def telecharger_archive(request, pk):
    """Télécharger un bulletin archivé"""
    from .services_archive import ArchivageService
    
    archive = get_object_or_404(
        ArchiveBulletin,
        pk=pk,
        bulletin__employe__entreprise=request.user.entreprise
    )
    
    contenu = ArchivageService.telecharger_archive(archive)
    if not contenu:
        messages.error(request, "Archive non disponible")
        return redirect('paie:liste_archives')
    
    response = HttpResponse(contenu, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="archive_{archive.employe_matricule}_{archive.periode_annee}{archive.periode_mois:02d}.pdf"'
    return response


@login_required
@entreprise_active_required
def verifier_integrite_archive(request, pk):
    """Vérifier l'intégrité d'une archive"""
    from .services_archive import ArchivageService
    
    archive = get_object_or_404(
        ArchiveBulletin,
        pk=pk,
        bulletin__employe__entreprise=request.user.entreprise
    )
    
    if ArchivageService.verifier_integrite(archive):
        messages.success(request, f"✓ Intégrité vérifiée pour {archive.employe_nom}")
    else:
        messages.error(request, f"✗ ALERTE: Intégrité compromise pour {archive.employe_nom}")
    
    return redirect('paie:liste_archives')


@login_required
@entreprise_active_required
def config_paie_entreprise(request):
    """Configuration des paramètres de paie par entreprise (HS, Congés, CNSS)"""
    from .models import ConfigurationPaieEntreprise
    from decimal import Decimal
    
    entreprise = request.user.entreprise
    config = ConfigurationPaieEntreprise.get_ou_creer(entreprise)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'code_travail':
            config.appliquer_mode_code_travail()
            messages.success(request, 'Configuration Code du Travail appliquée.')
        elif action == 'convention':
            config.appliquer_mode_convention()
            messages.success(request, 'Configuration Convention Collective appliquée.')
        elif action == 'save':
            # Fonction helper pour convertir en Decimal avec valeur par défaut
            def to_decimal(value, default):
                if value is None or value.strip() == '':
                    return Decimal(default)
                return Decimal(value)
            
            def to_int(value, default):
                if value is None or value.strip() == '':
                    return int(default)
                return int(value)
            
            # Heures supplémentaires
            config.mode_heures_sup = request.POST.get('mode_heures_sup', 'code_travail')
            config.taux_hs_4_premieres = to_decimal(request.POST.get('taux_hs_4_premieres'), '30')
            config.taux_hs_au_dela = to_decimal(request.POST.get('taux_hs_au_dela'), '60')
            config.taux_hs_nuit = to_decimal(request.POST.get('taux_hs_nuit'), '50')
            config.taux_hs_dimanche = to_decimal(request.POST.get('taux_hs_dimanche'), '100')
            config.taux_hs_ferie_nuit = to_decimal(request.POST.get('taux_hs_ferie_nuit'), '100')
            
            # Congés
            config.mode_conges = request.POST.get('mode_conges', 'code_travail')
            config.jours_conges_par_mois = to_decimal(request.POST.get('jours_conges_par_mois'), '1.5')
            config.jours_conges_anciennete = to_decimal(request.POST.get('jours_conges_anciennete'), '2')
            config.tranche_anciennete_annees = to_int(request.POST.get('tranche_anciennete_annees'), '5')
            
            # CNSS
            config.taux_cnss_employe = to_decimal(request.POST.get('taux_cnss_employe'), '5')
            config.taux_cnss_employeur = to_decimal(request.POST.get('taux_cnss_employeur'), '18')
            config.plancher_cnss = to_decimal(request.POST.get('plancher_cnss'), '550000')
            config.plafond_cnss = to_decimal(request.POST.get('plafond_cnss'), '2500000')
            
            # Charges patronales
            config.taux_versement_forfaitaire = to_decimal(request.POST.get('taux_versement_forfaitaire'), '6')
            config.taux_taxe_apprentissage = to_decimal(request.POST.get('taux_taxe_apprentissage'), '1.5')
            
            config.modifie_par = request.user
            config.save()
            messages.success(request, 'Configuration enregistrée avec succès.')
        
        return redirect('paie:config_entreprise')
    
    return render(request, 'paie/config_entreprise.html', {
        'config': config,
        'modes_hs': ConfigurationPaieEntreprise.MODES_HS,
        'modes_conges': ConfigurationPaieEntreprise.MODES_CONGES,
    })
