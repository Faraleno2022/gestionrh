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
    ElementSalaire, CumulPaie, HistoriquePaie, Constante, TrancheIRG,
    ParametrePaie
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
    """Calculer tous les bulletins d'une période"""
    periode = get_object_or_404(PeriodePaie, pk=pk, entreprise=request.user.entreprise)
    
    if periode.statut_periode not in ['ouverte', 'calculee']:
        messages.error(request, 'Cette période ne peut plus être calculée.')
        return redirect('paie:detail_periode', pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Supprimer les bulletins existants
                BulletinPaie.objects.filter(
                    periode=periode,
                    employe__entreprise=request.user.entreprise,
                ).delete()
                
                # Récupérer tous les employés actifs
                employes = Employe.objects.filter(
                    entreprise=request.user.entreprise,
                    statut_employe='actif'
                )
                
                bulletins_crees = 0
                erreurs = []
                
                for employe in employes:
                    try:
                        # Calculer le bulletin
                        moteur = MoteurCalculPaie(employe, periode)
                        bulletin = moteur.generer_bulletin(utilisateur=request.user)
                        bulletins_crees += 1
                    except Exception as e:
                        erreurs.append(f"{employe.matricule}: {str(e)}")
                
                # Mettre à jour le statut de la période
                periode.statut_periode = 'calculee'
                periode.save()
                
                if erreurs:
                    messages.warning(
                        request,
                        f'{bulletins_crees} bulletins créés. Erreurs: {", ".join(erreurs)}'
                    )
                else:
                    messages.success(
                        request,
                        f'{bulletins_crees} bulletins calculés avec succès.'
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
    
    # Ajouter CNSS et IRG
    retenues_data.append(["CNSS Employé (5%)", f"{bulletin.salaire_brut:,.0f}".replace(",", " "), "5%", f"{bulletin.cnss_employe:,.0f}".replace(",", " ")])
    retenues_data.append(["IRG (Impôt sur le Revenu)", "", "", f"{bulletin.irg:,.0f}".replace(",", " ")])
    
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
    p.drawString(2*cm, y - 1.4*cm, "IRG:")
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
    
    # Ajouter CNSS et IRG
    retenues_data.append(["CNSS Employé (5%)", f"{bulletin.salaire_brut:,.0f}".replace(",", " "), "5%", f"{bulletin.cnss_employe:,.0f}".replace(",", " ")])
    retenues_data.append(["IRG (Impôt sur le Revenu)", "", "", f"{bulletin.irg:,.0f}".replace(",", " ")])
    
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
    p.drawString(2*cm, y - 1.4*cm, "IRG:")
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
    
    # Récupérer tous les bulletins des périodes
    bulletins = BulletinPaie.objects.filter(
        periode__in=periodes,
        employe__entreprise=request.user.entreprise,
    ).select_related('employe', 'periode').order_by('periode__mois', 'employe__matricule')
    
    # Calcul des totaux
    totaux = bulletins.aggregate(
        total_brut=Sum('salaire_brut'),
        total_cnss_employe=Sum('cnss_employe'),
        total_cnss_employeur=Sum('cnss_employeur'),
        total_irg=Sum('irg'),
        total_net=Sum('net_a_payer')
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
def declarations_sociales(request):
    """Déclarations sociales (CNSS, IRG, INAM)"""
    # Filtres
    annee = request.GET.get('annee', timezone.now().year)
    mois = request.GET.get('mois')
    
    periodes = PeriodePaie.objects.filter(
        entreprise=request.user.entreprise,
        annee=annee,
        statut_periode__in=['validee', 'cloturee']
    )
    if mois:
        periodes = periodes.filter(mois=mois)
    
    bulletins = BulletinPaie.objects.filter(
        periode__in=periodes,
        statut_bulletin__in=['valide', 'paye'],
        employe__entreprise=request.user.entreprise,
    ).select_related('employe', 'periode')
    
    # Calculs pour CNSS
    declaration_cnss = {
        'total_salaries': bulletins.values('employe').distinct().count(),
        'masse_salariale': bulletins.aggregate(Sum('salaire_brut'))['salaire_brut__sum'] or 0,
        'cotisation_employe': bulletins.aggregate(Sum('cnss_employe'))['cnss_employe__sum'] or 0,
        'cotisation_employeur': bulletins.aggregate(Sum('cnss_employeur'))['cnss_employeur__sum'] or 0,
    }
    declaration_cnss['total_cotisation'] = (
        declaration_cnss['cotisation_employe'] + declaration_cnss['cotisation_employeur']
    )
    
    # Calculs pour IRG
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
        'detail_employes': detail_employes,
        'annee': int(annee),
        'mois': int(mois) if mois else None,
        'annees': annees,
        'periodes': periodes
    })


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
    
    # Rubriques disponibles
    rubriques = RubriquePaie.objects.filter(actif=True).order_by('type_rubrique', 'libelle_rubrique')
    
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
