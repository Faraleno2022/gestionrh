"""
Vues pour les rapports de paie avancés.
- Rapport masse salariale
- Export Excel / PDF du rapport
"""
import io
import json
from datetime import date
from decimal import Decimal

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone

from .models import BulletinPaie, PeriodePaie
from employes.models import Employe
from core.models import Service
from core.decorators import reauth_required, entreprise_active_required

# Imports optionnels
try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

MOIS_FR = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
           'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']


def _get_bulletins_filtrés(entreprise, annee, periode_type, mois=None, trimestre=None, service_id=None):
    """Retourne un queryset de bulletins selon les filtres."""
    qs = BulletinPaie.objects.filter(
        employe__entreprise=entreprise,
        annee_paie=annee,
        statut_bulletin__in=['calcule', 'valide', 'paye'],
    )
    if periode_type == 'mois' and mois:
        qs = qs.filter(mois_paie=mois)
    elif periode_type == 'trimestre' and trimestre:
        t = int(trimestre)
        mois_debut = (t - 1) * 3 + 1
        mois_fin = t * 3
        qs = qs.filter(mois_paie__gte=mois_debut, mois_paie__lte=mois_fin)
    # Filtre service
    if service_id:
        qs = qs.filter(employe__service_id=service_id)
    return qs


def _calcul_rapport(bulletins_qs):
    """Calcule les agrégats principaux à partir d'un queryset de bulletins."""
    agg = bulletins_qs.aggregate(
        nb=Count('id'),
        brut=Sum('salaire_brut'),
        cnss_sal=Sum('cnss_employe'),
        cnss_emp=Sum('cnss_employeur'),
        rts=Sum('irg'),
        net=Sum('net_a_payer'),
        vf=Sum('versement_forfaitaire'),
        ta=Sum('taxe_apprentissage'),
    )
    nb = agg['nb'] or 0
    brut = agg['brut'] or Decimal('0')
    cnss_sal = agg['cnss_sal'] or Decimal('0')
    cnss_emp = agg['cnss_emp'] or Decimal('0')
    rts = agg['rts'] or Decimal('0')
    net = agg['net'] or Decimal('0')
    vf = agg['vf'] or Decimal('0')
    ta = agg['ta'] or Decimal('0')
    charges_totales = cnss_sal + cnss_emp + rts + vf + ta
    ratio_charges = (charges_totales / brut * 100) if brut else Decimal('0')
    cout_moyen = (brut / nb) if nb else Decimal('0')
    return {
        'nb': nb,
        'brut': brut,
        'cnss_sal': cnss_sal,
        'cnss_emp': cnss_emp,
        'rts': rts,
        'net': net,
        'vf': vf,
        'ta': ta,
        'charges_totales': charges_totales,
        'ratio_charges': ratio_charges,
        'cout_moyen': cout_moyen,
    }


@login_required
@entreprise_active_required
@reauth_required
def rapport_masse_salariale(request):
    """Rapport de masse salariale avec filtres et graphiques."""
    entreprise = request.user.entreprise
    annee_courante = date.today().year

    # Paramètres de filtres
    annee = int(request.GET.get('annee', annee_courante))
    periode_type = request.GET.get('periode_type', 'annee')  # mois | trimestre | annee
    mois = request.GET.get('mois', '')
    trimestre = request.GET.get('trimestre', '')
    service_id = request.GET.get('service', '')

    # Services disponibles
    services = Service.objects.filter(
        entreprise=entreprise,
        actif=True,
    ).order_by('nom_service')

    # Bulletins filtrés
    bulletins = _get_bulletins_filtrés(
        entreprise, annee, periode_type,
        mois=mois or None,
        trimestre=trimestre or None,
        service_id=service_id or None,
    )

    # --- Tableau par service ---
    par_service = {}
    for b in bulletins.select_related('employe__service'):
        svc = b.employe.service
        svc_key = svc.pk if svc else 0
        svc_nom = str(svc) if svc else 'Sans service'
        if svc_key not in par_service:
            par_service[svc_key] = {
                'nom': svc_nom,
                'nb': 0,
                'brut': Decimal('0'),
                'cnss_sal': Decimal('0'),
                'rts': Decimal('0'),
                'net': Decimal('0'),
                'cnss_emp': Decimal('0'),
            }
        r = par_service[svc_key]
        r['nb'] += 1
        r['brut'] += b.salaire_brut or Decimal('0')
        r['cnss_sal'] += b.cnss_employe or Decimal('0')
        r['rts'] += b.irg or Decimal('0')
        r['net'] += b.net_a_payer or Decimal('0')
        r['cnss_emp'] += b.cnss_employeur or Decimal('0')

    tableau_services = sorted(par_service.values(), key=lambda x: -x['brut'])

    # --- Évolution mensuelle (tous les mois de l'année) ---
    evolution_data = []
    labels_mois = []
    for m in range(1, 13):
        bm = BulletinPaie.objects.filter(
            employe__entreprise=entreprise,
            annee_paie=annee,
            mois_paie=m,
            statut_bulletin__in=['calcule', 'valide', 'paye'],
        )
        if service_id:
            bm = bm.filter(employe__service_id=service_id)
        agg_m = bm.aggregate(brut=Sum('salaire_brut'), net=Sum('net_a_payer'), nb=Count('id'))
        evolution_data.append({
            'mois': m,
            'label': MOIS_FR[m][:3],
            'brut': float(agg_m['brut'] or 0),
            'net': float(agg_m['net'] or 0),
            'nb': agg_m['nb'] or 0,
        })
        labels_mois.append(MOIS_FR[m][:3])

    # --- Top 10 coûts salariaux ---
    top10 = bulletins.order_by('-salaire_brut').select_related('employe')[:10]
    top10_data = []
    for b in top10:
        top10_data.append({
            'employe': f"{b.employe.nom} {b.employe.prenoms}",
            'matricule': b.employe.matricule,
            'service': str(b.employe.service) if b.employe.service else '-',
            'brut': b.salaire_brut or Decimal('0'),
            'net': b.net_a_payer or Decimal('0'),
        })

    # --- Indicateurs globaux ---
    indicateurs = _calcul_rapport(bulletins)

    # --- Comparaison N vs N-1 ---
    bulletins_n1 = BulletinPaie.objects.filter(
        employe__entreprise=entreprise,
        annee_paie=annee - 1,
        statut_bulletin__in=['calcule', 'valide', 'paye'],
    )
    if service_id:
        bulletins_n1 = bulletins_n1.filter(employe__service_id=service_id)
    indic_n1 = _calcul_rapport(bulletins_n1)
    evol_brut = None
    if indic_n1['brut'] and indic_n1['brut'] > 0:
        evol_brut = float((indicateurs['brut'] - indic_n1['brut']) / indic_n1['brut'] * 100)

    # Années disponibles
    annees_dispo = BulletinPaie.objects.filter(
        employe__entreprise=entreprise
    ).values_list('annee_paie', flat=True).distinct().order_by('-annee_paie')

    # Données JSON pour Chart.js
    chart_labels = json.dumps(labels_mois)
    chart_brut = json.dumps([d['brut'] for d in evolution_data])
    chart_net = json.dumps([d['net'] for d in evolution_data])

    context = {
        'annee': annee,
        'annee_n1': annee - 1,
        'periode_type': periode_type,
        'mois': mois,
        'trimestre': trimestre,
        'service_id': service_id,
        'services': services,
        'tableau_services': tableau_services,
        'evolution_data': evolution_data,
        'top10': top10_data,
        'indicateurs': indicateurs,
        'indic_n1': indic_n1,
        'evol_brut': evol_brut,
        'annees_dispo': annees_dispo,
        'chart_labels': chart_labels,
        'chart_brut': chart_brut,
        'chart_net': chart_net,
        'mois_fr': MOIS_FR,
        'trimestres': [1, 2, 3, 4],
        'mois_liste': list(range(1, 13)),
    }
    return render(request, 'paie/rapport_masse_salariale.html', context)


@login_required
@entreprise_active_required
@reauth_required
def rapport_masse_salariale_excel(request):
    """Export Excel du rapport masse salariale."""
    if not OPENPYXL_AVAILABLE:
        return HttpResponse("openpyxl non disponible", status=500)

    entreprise = request.user.entreprise
    annee = int(request.GET.get('annee', date.today().year))
    periode_type = request.GET.get('periode_type', 'annee')
    mois = request.GET.get('mois', '')
    trimestre = request.GET.get('trimestre', '')
    service_id = request.GET.get('service', '')

    bulletins = _get_bulletins_filtrés(
        entreprise, annee, periode_type,
        mois=mois or None, trimestre=trimestre or None, service_id=service_id or None,
    )

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Masse Salariale"

    # Styles
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    center = Alignment(horizontal='center')
    right = Alignment(horizontal='right')
    thin = Side(style='thin')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    def cell_style(cell, bold=False, fill_color=None, align=None):
        if bold:
            cell.font = Font(bold=True)
        if fill_color:
            cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
        if align:
            cell.alignment = align
        cell.border = border

    # Titre
    ws.merge_cells('A1:G1')
    ws['A1'] = f"RAPPORT MASSE SALARIALE - {annee}"
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = center

    ws.merge_cells('A2:G2')
    ws['A2'] = f"Généré le {date.today().strftime('%d/%m/%Y')}"
    ws['A2'].alignment = center

    # Entête tableau par service
    row = 4
    headers = ['Service', 'Nb Employés', 'Masse Brute', 'CNSS Salarié', 'RTS', 'CNSS Patronal', 'Masse Nette']
    for col, h in enumerate(headers, 1):
        c = ws.cell(row=row, column=col, value=h)
        c.font = header_font
        c.fill = header_fill
        c.alignment = center
        c.border = border

    # Données par service
    par_service = {}
    for b in bulletins.select_related('employe__service'):
        svc = b.employe.service
        svc_key = svc.pk if svc else 0
        svc_nom = str(svc) if svc else 'Sans service'
        if svc_key not in par_service:
            par_service[svc_key] = {'nom': svc_nom, 'nb': 0, 'brut': Decimal('0'),
                                     'cnss_sal': Decimal('0'), 'rts': Decimal('0'),
                                     'net': Decimal('0'), 'cnss_emp': Decimal('0')}
        r = par_service[svc_key]
        r['nb'] += 1
        r['brut'] += b.salaire_brut or Decimal('0')
        r['cnss_sal'] += b.cnss_employe or Decimal('0')
        r['rts'] += b.irg or Decimal('0')
        r['net'] += b.net_a_payer or Decimal('0')
        r['cnss_emp'] += b.cnss_employeur or Decimal('0')

    row = 5
    for sv in sorted(par_service.values(), key=lambda x: -x['brut']):
        ws.cell(row=row, column=1, value=sv['nom']).border = border
        ws.cell(row=row, column=2, value=sv['nb']).border = border
        ws.cell(row=row, column=3, value=float(sv['brut'])).border = border
        ws.cell(row=row, column=4, value=float(sv['cnss_sal'])).border = border
        ws.cell(row=row, column=5, value=float(sv['rts'])).border = border
        ws.cell(row=row, column=6, value=float(sv['cnss_emp'])).border = border
        ws.cell(row=row, column=7, value=float(sv['net'])).border = border
        row += 1

    # Format colonnes
    for col in range(3, 8):
        for r in range(5, row):
            ws.cell(row=r, column=col).number_format = '#,##0'

    for col_letter, width in zip('ABCDEFG', [30, 14, 18, 18, 18, 18, 18]):
        ws.column_dimensions[col_letter].width = width

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="masse_salariale_{annee}.xlsx"'
    return response


@login_required
@entreprise_active_required
@reauth_required
def rapport_masse_salariale_pdf(request):
    """Export PDF du rapport masse salariale."""
    if not REPORTLAB_AVAILABLE:
        return HttpResponse("ReportLab non disponible", status=500)

    entreprise = request.user.entreprise
    annee = int(request.GET.get('annee', date.today().year))
    periode_type = request.GET.get('periode_type', 'annee')
    mois = request.GET.get('mois', '')
    trimestre = request.GET.get('trimestre', '')
    service_id = request.GET.get('service', '')

    bulletins = _get_bulletins_filtrés(
        entreprise, annee, periode_type,
        mois=mois or None, trimestre=trimestre or None, service_id=service_id or None,
    )
    indicateurs = _calcul_rapport(bulletins)

    # Tableau par service
    par_service = {}
    for b in bulletins.select_related('employe__service'):
        svc = b.employe.service
        svc_key = svc.pk if svc else 0
        svc_nom = str(svc) if svc else 'Sans service'
        if svc_key not in par_service:
            par_service[svc_key] = {'nom': svc_nom, 'nb': 0, 'brut': Decimal('0'),
                                     'cnss_sal': Decimal('0'), 'rts': Decimal('0'),
                                     'net': Decimal('0')}
        r = par_service[svc_key]
        r['nb'] += 1
        r['brut'] += b.salaire_brut or Decimal('0')
        r['cnss_sal'] += b.cnss_employe or Decimal('0')
        r['rts'] += b.irg or Decimal('0')
        r['net'] += b.net_a_payer or Decimal('0')

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle('Title', parent=styles['Title'],
                                  fontSize=16, spaceAfter=6, alignment=TA_CENTER)
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'],
                                fontSize=10, spaceAfter=12, alignment=TA_CENTER)
    section_style = ParagraphStyle('Section', parent=styles['Normal'],
                                    fontSize=12, fontName='Helvetica-Bold',
                                    spaceAfter=6, spaceBefore=12)

    elements.append(Paragraph(f"RAPPORT MASSE SALARIALE - {annee}", title_style))
    elements.append(Paragraph(f"Généré le {date.today().strftime('%d/%m/%Y')}", sub_style))

    # Indicateurs globaux
    elements.append(Paragraph("Indicateurs globaux", section_style))
    indic_data = [
        ['Indicateur', 'Valeur'],
        ['Nombre de bulletins', str(indicateurs['nb'])],
        ['Masse salariale brute', f"{indicateurs['brut']:,.0f} GNF"],
        ['CNSS salarié total', f"{indicateurs['cnss_sal']:,.0f} GNF"],
        ['RTS total', f"{indicateurs['rts']:,.0f} GNF"],
        ['Masse salariale nette', f"{indicateurs['net']:,.0f} GNF"],
        ['Coût moyen / employé', f"{indicateurs['cout_moyen']:,.0f} GNF"],
        ['Ratio charges / brut', f"{indicateurs['ratio_charges']:.1f}%"],
    ]
    t_indic = Table(indic_data, colWidths=[8*cm, 7*cm])
    t_indic.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#EBF3FF')]),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    elements.append(t_indic)

    # Tableau par service
    elements.append(Paragraph("Répartition par service", section_style))
    svc_header = ['Service', 'Nb Emp.', 'Masse Brute', 'CNSS Sal.', 'RTS', 'Masse Nette']
    svc_rows = [svc_header]
    for sv in sorted(par_service.values(), key=lambda x: -x['brut']):
        svc_rows.append([
            sv['nom'],
            str(sv['nb']),
            f"{sv['brut']:,.0f}",
            f"{sv['cnss_sal']:,.0f}",
            f"{sv['rts']:,.0f}",
            f"{sv['net']:,.0f}",
        ])
    t_svc = Table(svc_rows, colWidths=[7*cm, 2.5*cm, 4*cm, 3.5*cm, 3.5*cm, 4*cm])
    t_svc.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#EBF3FF')]),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
    ]))
    elements.append(t_svc)

    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="masse_salariale_{annee}.pdf"'
    return response
