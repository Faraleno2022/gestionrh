"""
Utilitaires de paie - Génération PDF de bulletins
"""
import io
import os
from decimal import Decimal
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os as _os

# Enregistrer Arial avec support UTF-8/accents
_FONT_DIR = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'static', 'fonts')
try:
    pdfmetrics.registerFont(TTFont('Arial', _os.path.join(_FONT_DIR, 'Arial.ttf')))
    pdfmetrics.registerFont(TTFont('Arial-Bold', _os.path.join(_FONT_DIR, 'Arial-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('Arial-Italic', _os.path.join(_FONT_DIR, 'Arial-Italic.ttf')))
    _FONT_NORMAL = 'Arial'
    _FONT_BOLD   = 'Arial-Bold'
    _FONT_ITALIC = 'Arial-Italic'
except Exception:
    _FONT_NORMAL = _FONT_NORMAL
    _FONT_BOLD   = _FONT_BOLD
    _FONT_ITALIC = 'Helvetica-Oblique'
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from django.utils import timezone


def calculer_detail_tranches_rts(base_rts):
    """
    Calcule le détail progressif RTS par tranche à partir de la base imposable.
    Barème CGI 2022 (6 tranches).
    
    Returns:
        list of dict avec clés: borne_inf, borne_sup, taux, base_tranche, impot_tranche
    """
    from decimal import ROUND_HALF_UP
    
    base_rts = Decimal(str(base_rts or 0))
    if base_rts <= 0:
        return []
    
    # Charger les tranches depuis la BDD si possible
    tranches_db = []
    try:
        from .models import TrancheRTS
        annee = timezone.now().year
        tranches_db = list(TrancheRTS.objects.filter(
            annee_validite=annee, actif=True
        ).order_by('numero_tranche').values(
            'borne_inferieure', 'borne_superieure', 'taux_irg'
        ))
        if not tranches_db:
            tranches_db = list(TrancheRTS.objects.filter(
                actif=True
            ).order_by('-annee_validite', 'numero_tranche'))
            if tranches_db:
                annee_found = tranches_db[0].get('annee_validite') if isinstance(tranches_db[0], dict) else tranches_db[0].annee_validite
                tranches_db = list(TrancheRTS.objects.filter(
                    annee_validite=annee_found, actif=True
                ).order_by('numero_tranche').values(
                    'borne_inferieure', 'borne_superieure', 'taux_irg'
                ))
    except Exception:
        tranches_db = []
    
    # Fallback: barème CGI 2022
    if not tranches_db:
        tranches_db = [
            {'borne_inferieure': Decimal('0'), 'borne_superieure': Decimal('1000000'), 'taux_irg': Decimal('0')},
            {'borne_inferieure': Decimal('1000000'), 'borne_superieure': Decimal('3000000'), 'taux_irg': Decimal('5')},
            {'borne_inferieure': Decimal('3000000'), 'borne_superieure': Decimal('5000000'), 'taux_irg': Decimal('8')},
            {'borne_inferieure': Decimal('5000000'), 'borne_superieure': Decimal('10000000'), 'taux_irg': Decimal('10')},
            {'borne_inferieure': Decimal('10000000'), 'borne_superieure': Decimal('20000000'), 'taux_irg': Decimal('15')},
            {'borne_inferieure': Decimal('20000000'), 'borne_superieure': None, 'taux_irg': Decimal('20')},
        ]
    
    # Normaliser les bornes (éliminer les gaps de 1 GNF)
    seuils = []
    for i, t in enumerate(tranches_db):
        b_inf = Decimal(str(t['borne_inferieure']))
        b_sup = t.get('borne_superieure')
        taux = Decimal(str(t['taux_irg']))
        if i > 0 and seuils:
            prev_sup = seuils[-1][1]
            if prev_sup is not None and b_inf > prev_sup and b_inf <= prev_sup + 2:
                b_inf = prev_sup
        if b_sup is not None:
            b_sup = Decimal(str(b_sup))
        seuils.append((b_inf, b_sup, taux))
    
    # Calcul progressif
    detail = []
    for b_inf, b_sup, taux in seuils:
        if base_rts <= b_inf:
            break
        if b_sup is not None:
            base_tranche = min(base_rts, b_sup) - b_inf
        else:
            base_tranche = base_rts - b_inf
        if base_tranche <= 0:
            continue
        impot = (base_tranche * taux / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        detail.append({
            'borne_inf': b_inf,
            'borne_sup': b_sup,
            'taux': taux,
            'base_tranche': base_tranche,
            'impot_tranche': impot,
        })
    
    return detail


def generer_bulletin_pdf(bulletin):
    """
    Génère le PDF d'un bulletin de paie et retourne les bytes du PDF.
    
    Args:
        bulletin: Instance BulletinPaie
        
    Returns:
        bytes: Contenu du fichier PDF
    """
    from .models import LigneBulletin
    
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
    
    # Titre centré
    p.setFont(_FONT_BOLD, 11)
    p.drawCentredString(width/2, y, "RÉPUBLIQUE DE GUINÉE")
    y -= 0.4*cm
    p.setFont(_FONT_ITALIC, 8)
    p.drawCentredString(width/2, y, "Travail - Justice - Solidarité")
    y -= 0.5*cm
    
    # Nom entreprise
    p.setFont(_FONT_BOLD, 12)
    nom_entreprise = entreprise.nom_entreprise if entreprise else "ENTREPRISE"
    p.drawCentredString(width/2, y, nom_entreprise)
    y -= 0.6*cm
    
    # Titre bulletin
    p.setFont(_FONT_BOLD, 14)
    p.drawCentredString(width/2, y, "BULLETIN DE PAIE")
    y -= 0.4*cm
    
    # Ligne de séparation
    p.setStrokeColor(colors.HexColor("#ce1126"))
    p.setLineWidth(2)
    p.line(1.5*cm, y, width - 1.5*cm, y)
    y -= 0.6*cm
    
    # Infos bulletin sur une ligne
    p.setFont(_FONT_NORMAL, 9)
    p.setFillColor(colors.black)
    p.drawString(1.5*cm, y, f"N°: {bulletin.numero_bulletin}")
    p.drawCentredString(width/2, y, f"Période: {bulletin.periode}")
    p.drawRightString(width - 1.5*cm, y, f"Date: {bulletin.date_calcul.strftime('%d/%m/%Y') if bulletin.date_calcul else '-'}")
    y -= 0.35*cm
    # Dates de la période
    p.setFont(_FONT_NORMAL, 8)
    periode_detail = f"Du {bulletin.periode.date_debut.strftime('%d/%m/%Y')} au {bulletin.periode.date_fin.strftime('%d/%m/%Y')}" if bulletin.periode.date_debut and bulletin.periode.date_fin else ""
    p.drawCentredString(width/2, y, periode_detail)
    y -= 0.6*cm
    
    # === INFORMATIONS EMPLOYÉ ===
    p.setFillColor(colors.HexColor("#ce1126"))
    p.setFont(_FONT_BOLD, 9)
    p.drawString(1.5*cm, y, "INFORMATIONS EMPLOYÉ")
    p.setFillColor(colors.black)
    y -= 0.5*cm
    
    emp = bulletin.employe
    
    # Calcul de l'ancienneté
    anciennete_str = "-"
    if emp.date_embauche:
        from datetime import date as date_cls
        ref_date = date_cls(bulletin.annee_paie, bulletin.mois_paie, 1)
        delta = ref_date - emp.date_embauche
        annees_anc = delta.days // 365
        mois_anc = (delta.days % 365) // 30
        if annees_anc > 0:
            anciennete_str = f"{annees_anc} an{'s' if annees_anc > 1 else ''} {mois_anc} mois"
        else:
            anciennete_str = f"{mois_anc} mois"
    
    # Récupération des congés
    from temps_travail.models import SoldeConge
    solde_conge = SoldeConge.objects.filter(employe=emp, annee=bulletin.annee_paie).first()
    conges_acquis = solde_conge.conges_acquis if solde_conge else Decimal('0')
    conges_pris = solde_conge.conges_pris if solde_conge else Decimal('0')
    conges_restants = solde_conge.conges_restants if solde_conge else Decimal('0')
    
    infos_emp = [
        ["Matricule:", emp.matricule or "-", "N° CNSS:", emp.num_cnss_individuel or "-"],
        ["Nom et Prénoms:", f"{emp.nom} {emp.prenoms}", "Ancienneté:", anciennete_str],
        ["Poste:", str(emp.poste or "-"), "Service:", str(emp.service or "-")],
        ["Date embauche:", emp.date_embauche.strftime('%d/%m/%Y') if emp.date_embauche else "-", "Mode paiement:", emp.mode_paiement or "-"],
        ["Congés acquis:", f"{conges_acquis:g} j", "Congés pris:", f"{conges_pris:g} j"],
        ["Solde congés:", f"{conges_restants:g} j", "Nature contrat:", dict(emp.TYPES_CONTRATS).get(emp.type_contrat, emp.type_contrat or "-")],
    ]
    
    for row in infos_emp:
        p.setFont(_FONT_BOLD, 8)
        p.drawString(1.5*cm, y, row[0])
        p.setFont(_FONT_NORMAL, 8)
        p.drawString(4*cm, y, str(row[1]))
        if row[2]:
            p.setFont(_FONT_BOLD, 8)
            p.drawString(11*cm, y, row[2])
            p.setFont(_FONT_NORMAL, 8)
            p.drawString(14*cm, y, str(row[3]))
        y -= 0.4*cm
    
    y -= 0.3*cm
    
    # === GAINS ===
    p.setFillColor(colors.HexColor("#28a745"))
    p.setFont(_FONT_BOLD, 9)
    p.drawString(1.5*cm, y, "GAINS ET RÉMUNÉRATIONS")
    p.setFillColor(colors.black)
    y -= 0.3*cm
    
    # Tableau des gains (5 colonnes avec Nbre pour les heures)
    gains_data = [["Libellé", "Nbre", "Base", "Taux", "Montant"]]
    for g in gains:
        nbre_str = f"{g.nombre:g}" if g.nombre and g.nombre != 1 else ""
        gains_data.append([
            g.rubrique.libelle_rubrique[:35],
            nbre_str,
            f"{g.base:,.0f}".replace(",", " ") if g.base else "-",
            f"{g.taux}%" if g.taux else "-",
            f"{g.montant:,.0f}".replace(",", " ")
        ])
    gains_data.append(["TOTAL BRUT", "", "", "", f"{bulletin.salaire_brut:,.0f} GNF".replace(",", " ")])
    
    row_height = 14
    gains_table = Table(gains_data, colWidths=[6.5*cm, 1.5*cm, 3*cm, 2*cm, 4*cm], rowHeights=row_height)
    gains_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#28a745")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), _FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#d4edda")),
        ('FONTNAME', (0, -1), (-1, -1), _FONT_BOLD),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    table_height = len(gains_data) * row_height
    gains_table.wrapOn(p, width, height)
    gains_table.drawOn(p, 1.5*cm, y - table_height)
    y -= table_height + 0.5*cm
    
    # === DÉTAIL HEURES SUPPLÉMENTAIRES ===
    hs_30 = getattr(bulletin, 'heures_supplementaires_30', 0) or 0
    hs_60 = getattr(bulletin, 'heures_supplementaires_60', 0) or 0
    hs_nuit = getattr(bulletin, 'heures_nuit', 0) or 0
    hs_feries = getattr(bulletin, 'heures_feries', 0) or 0
    prime_hs = getattr(bulletin, 'prime_heures_sup', 0) or 0
    prime_nuit = getattr(bulletin, 'prime_nuit', 0) or 0
    prime_feries = getattr(bulletin, 'prime_feries', 0) or 0
    total_hs_heures = float(hs_30) + float(hs_60) + float(hs_nuit) + float(hs_feries)
    
    if total_hs_heures > 0 or float(prime_hs) > 0:
        p.setFont(_FONT_BOLD, 7)
        p.setFillColor(colors.HexColor("#6c757d"))
        p.drawString(1.5*cm, y, "DÉTAIL HEURES SUPPLÉMENTAIRES (Code du Travail Art. 221)")
        p.setFillColor(colors.black)
        y -= 0.25*cm
        
        # Calcul des montants individuels (salaire_base / 173,33 × h × coefficient)
        _sal_h = Decimal(str(bulletin.salaire_base or 0)) / Decimal('173.33')
        _montant_30 = int(_sal_h * Decimal(str(hs_30)) * Decimal('1.30'))
        _montant_60 = int(_sal_h * Decimal(str(hs_60)) * Decimal('1.60'))

        hs_detail_data = [["Type", "Heures", "Majoration", "Montant"]]
        if float(hs_30) > 0:
            hs_detail_data.append(["4 prem. HS/sem.", f"{hs_30:g}h", "+30% (130%)",
                                    f"{_montant_30:,.0f}".replace(",", " ")])
        if float(hs_60) > 0:
            hs_detail_data.append(["Au-delà 4 HS/sem.", f"{hs_60:g}h", "+60% (160%)",
                                    f"{_montant_60:,.0f}".replace(",", " ")])
        if float(hs_nuit) > 0:
            hs_detail_data.append(["Heures de nuit (20h-6h)", f"{hs_nuit:g}h", "+20% (120%)",
                                    f"{prime_nuit:,.0f}".replace(",", " ")])
        if float(hs_feries) > 0:
            hs_detail_data.append(["Jours fériés", f"{hs_feries:g}h", "+60/100%",
                                    f"{prime_feries:,.0f}".replace(",", " ")])

        total_prime = float(prime_hs) + float(prime_nuit) + float(prime_feries)
        hs_detail_data.append(["", f"{total_hs_heures:g}h", "Total HS:",
                                f"{total_prime:,.0f} GNF".replace(",", " ")])
        
        hs_row_h = 12
        hs_table = Table(hs_detail_data, colWidths=[5.5*cm, 2*cm, 4.5*cm, 5*cm], rowHeights=hs_row_h)
        nb_hs_rows = len(hs_detail_data)
        hs_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#6c757d")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), _FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#dee2e6")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, -1), (-1, -1), _FONT_BOLD),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#f8f9fa")),
        ]))
        
        hs_table_h = nb_hs_rows * hs_row_h
        hs_table.wrapOn(p, width, height)
        hs_table.drawOn(p, 1.5*cm, y - hs_table_h)
        y -= hs_table_h + 0.35*cm
    else:
        y += 0.35*cm
    
    # === RETENUES ===
    p.setFillColor(colors.HexColor("#dc3545"))
    p.setFont(_FONT_BOLD, 9)
    p.drawString(1.5*cm, y, "RETENUES ET COTISATIONS")
    p.setFillColor(colors.black)
    y -= 0.4*cm
    
    retenues_data = [["Libellé", "Base", "Taux", "Montant"]]
    cnss_irg_codes = ['CNSS', 'IRG', 'RTS', 'IRS', 'IRPP']
    for r in retenues:
        code = r.rubrique.code_rubrique.upper() if r.rubrique.code_rubrique else ''
        libelle = r.rubrique.libelle_rubrique.upper() if r.rubrique.libelle_rubrique else ''
        is_cnss_irg = any(c in code or c in libelle for c in cnss_irg_codes)
        if not is_cnss_irg:
            retenues_data.append([
                r.rubrique.libelle_rubrique[:35],
                f"{r.base:,.0f}".replace(",", " ") if r.base else "-",
                f"{r.taux}%" if r.taux else "-",
                f"{r.montant:,.0f}".replace(",", " ")
            ])
    
    # Ajouter CNSS et RTS
    base_cnss = min(bulletin.salaire_brut, 2500000)
    retenues_data.append(["CNSS Employé (5%)", f"{base_cnss:,.0f}".replace(",", " "), "5%", f"{bulletin.cnss_employe:,.0f}".replace(",", " ")])
    base_rts_val = getattr(bulletin, 'base_rts', 0) or 0
    taux_eff_rts_val = getattr(bulletin, 'taux_effectif_rts', 0) or 0
    rts_base_str = f"{base_rts_val:,.0f}".replace(",", " ") if base_rts_val else "-"
    rts_taux_str = f"{taux_eff_rts_val:.2f}%" if taux_eff_rts_val else "-"
    retenues_data.append(["RTS (Impôt sur le Revenu)", rts_base_str, rts_taux_str, f"{bulletin.irg:,.0f}".replace(",", " ")])
    
    retenues_table = Table(retenues_data, colWidths=[8*cm, 3*cm, 2*cm, 4*cm], rowHeights=row_height)
    retenues_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#dc3545")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), _FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    table_height = len(retenues_data) * row_height
    retenues_table.wrapOn(p, width, height)
    retenues_table.drawOn(p, 1.5*cm, y - table_height)
    y -= table_height + 0.5*cm
    
    # === DÉTAIL CALCUL RTS (barème progressif) ===
    detail_rts = calculer_detail_tranches_rts(base_rts_val)
    if detail_rts:
        p.setFont(_FONT_BOLD, 7)
        p.setFillColor(colors.HexColor("#6c757d"))
        p.drawString(1.5*cm, y, f"DÉTAIL RTS — Barème progressif sur base imposable: {base_rts_val:,.0f} GNF".replace(",", " "))
        p.setFillColor(colors.black)
        y -= 0.25*cm
        
        rts_detail_data = [["Tranche", "Taux", "Impôt"]]
        cumul_impot = Decimal('0')
        for i, t in enumerate(detail_rts, start=1):
            rts_detail_data.append([
                f"RTS {i}",
                f"{t['taux']:g}%",
                f"{t['impot_tranche']:,.0f}".replace(",", " "),
            ])
            cumul_impot += t['impot_tranche']
        rts_detail_data.append(["", "Total RTS:", f"{cumul_impot:,.0f} GNF".replace(",", " ")])
        
        rts_row_h = 12
        rts_table = Table(rts_detail_data, colWidths=[3*cm, 3*cm, 11*cm], rowHeights=rts_row_h)
        nb_rows = len(rts_detail_data)
        rts_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#6c757d")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), _FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#dee2e6")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, -1), (-1, -1), _FONT_BOLD),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#f8f9fa")),
        ]))
        
        rts_table_h = nb_rows * rts_row_h
        rts_table.wrapOn(p, width, height)
        rts_table.drawOn(p, 1.5*cm, y - rts_table_h)
        y -= rts_table_h + 0.4*cm
    else:
        y -= 0.2*cm
    
    # === RÉCAPITULATIF ===
    rappel = getattr(bulletin, 'rappel_salaire', 0) or 0
    trop_percu = getattr(bulletin, 'retenue_trop_percu', 0) or 0
    has_rappel = rappel > 0
    has_trop_percu = trop_percu > 0
    extra_lines = (1 if has_rappel else 0) + (1 if has_trop_percu else 0)
    recap_height = 2.1*cm + extra_lines * 0.4*cm
    p.setStrokeColor(colors.HexColor("#ce1126"))
    p.setLineWidth(2)
    p.rect(1.5*cm, y - recap_height, width - 3*cm, recap_height, stroke=1, fill=0)
    
    p.setFont(_FONT_BOLD, 10)
    p.setFillColor(colors.black)
    p.drawString(2*cm, y - 0.5*cm, "SALAIRE BRUT:")
    p.drawRightString(width - 2*cm, y - 0.5*cm, f"{bulletin.salaire_brut:,.0f} GNF".replace(",", " "))
    
    # CNSS et RTS alignés sur la même ligne
    p.setFont(_FONT_NORMAL, 8)
    p.setFillColor(colors.HexColor("#dc3545"))
    mid_x = width / 2
    p.drawString(2*cm, y - 1*cm, f"CNSS (5%): -{bulletin.cnss_employe:,.0f}".replace(",", " "))
    p.drawString(mid_x, y - 1*cm, f"RTS ({taux_eff_rts_val:.2f}%): -{bulletin.irg:,.0f}".replace(",", " "))
    p.drawRightString(width - 2*cm, y - 1*cm, f"Total retenues: -{bulletin.cnss_employe + bulletin.irg:,.0f} GNF".replace(",", " "))
    
    offset_y = 1*cm
    if has_rappel:
        offset_y += 0.4*cm
        p.setFillColor(colors.HexColor("#007bff"))
        p.drawString(2*cm, y - offset_y, "Rappel/Complément salaire précédent:")
        p.drawRightString(width - 2*cm, y - offset_y, f"+ {rappel:,.0f} GNF".replace(",", " "))
    if has_trop_percu:
        offset_y += 0.4*cm
        p.setFillColor(colors.HexColor("#dc3545"))
        p.drawString(2*cm, y - offset_y, "Retenue trop-perçu salaire précédent:")
        p.drawRightString(width - 2*cm, y - offset_y, f"- {trop_percu:,.0f} GNF".replace(",", " "))
    
    p.setFillColor(colors.HexColor("#28a745"))
    p.setFont(_FONT_BOLD, 11)
    p.drawString(2*cm, y - offset_y - 0.7*cm, "NET À PAYER:")
    p.drawRightString(width - 2*cm, y - offset_y - 0.7*cm, f"{bulletin.net_a_payer:,.0f} GNF".replace(",", " "))
    p.setFillColor(colors.black)
    
    y -= recap_height + 0.5*cm
    
    # === CHARGES PATRONALES ===
    vf = getattr(bulletin, 'versement_forfaitaire', 0) or 0
    ta = getattr(bulletin, 'taxe_apprentissage', 0) or 0
    onfpp = getattr(bulletin, 'contribution_onfpp', 0) or 0
    total_charges = bulletin.cnss_employeur + vf + ta + onfpp
    
    p.setFont(_FONT_BOLD, 8)
    p.drawString(1.5*cm, y, "CHARGES PATRONALES:")
    y -= 0.35*cm
    p.setFont(_FONT_NORMAL, 6.5)
    p.drawString(1.5*cm, y, f"CNSS 18%: {bulletin.cnss_employeur:,.0f}".replace(",", " "))
    p.drawString(5.5*cm, y, f"VF 6%: {vf:,.0f}".replace(",", " "))
    p.drawString(9*cm, y, f"TA 1,5%: {ta:,.0f}".replace(",", " "))
    p.drawString(12.5*cm, y, f"ONFPP 1,5%: {onfpp:,.0f}".replace(",", " "))
    p.setFont(_FONT_BOLD, 7)
    p.drawRightString(width - 1.5*cm, y, f"Total: {total_charges:,.0f} GNF".replace(",", " "))
    y -= 0.3*cm
    
    # === ZONE DE SIGNATURES ===
    y -= 1.2*cm
    p.setFont(_FONT_BOLD, 8)
    p.drawString(2*cm, y, "L'Employeur")
    p.drawString(12*cm, y, "L'Employé(e)")
    y -= 0.4*cm
    p.setFont(_FONT_NORMAL, 7)
    if entreprise:
        p.drawString(2*cm, y, entreprise.nom_entreprise or '')
    p.drawString(12*cm, y, f"{emp.nom} {emp.prenoms}")
    # Lignes de signature
    y -= 1.5*cm
    p.setDash(3, 3)
    p.line(2*cm, y, 7*cm, y)
    p.line(12*cm, y, 17*cm, y)
    p.setDash()
    y -= 0.3*cm
    p.setFont(_FONT_NORMAL, 6)
    p.drawCentredString(4.5*cm, y, "Date et signature")
    p.drawCentredString(14.5*cm, y, "Lu et approuvé, date et signature")
    
    # === PIED DE PAGE ===
    p.setFont(_FONT_NORMAL, 7)
    p.drawCentredString(width/2, 2.2*cm, "Ce bulletin est conforme à la législation guinéenne en vigueur.")
    if entreprise:
        p.drawCentredString(width/2, 1.7*cm, f"{entreprise.nom_entreprise} - {entreprise.adresse or ''} - Tél: {entreprise.telephone or ''}")
        p.drawCentredString(width/2, 1.3*cm, f"NIF: {entreprise.nif or '-'} - CNSS: {entreprise.num_cnss or '-'}")
    
    p.drawCentredString(width/2, 0.8*cm, f"Document généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')}")
    
    # Finaliser le PDF
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer.read()


def generer_bulletin_pdf_sdbk(bulletin):
    """
    Génère le PDF d'un bulletin de paie au format SDBK.
    Modèle 2 : tableau unifié Part Salariale / Part Patronale,
    boîte info en haut à droite, pied récapitulatif avec Net à payer.
    """
    from .models import LigneBulletin

    lignes = LigneBulletin.objects.filter(bulletin=bulletin).select_related('rubrique').order_by('rubrique__ordre_affichage')
    gains   = lignes.filter(rubrique__type_rubrique='gain')

    buffer = io.BytesIO()
    p      = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    entreprise = bulletin.employe.entreprise
    emp        = bulletin.employe

    # ── Ancienneté ──────────────────────────────────────────────────────────
    anciennete_str = "-"
    if emp.date_embauche:
        from datetime import date as _d
        ref  = _d(bulletin.annee_paie, bulletin.mois_paie, 1)
        diff = ref - emp.date_embauche
        ans  = diff.days // 365
        mois = (diff.days % 365) // 30
        anciennete_str = f"{ans:02d} ans et Mois {mois:02d}"

    # ── Congés ───────────────────────────────────────────────────────────────
    from temps_travail.models import SoldeConge
    solde = SoldeConge.objects.filter(employe=emp, annee=bulletin.annee_paie).first()
    c_acquis   = float(solde.conges_acquis   if solde else 0)
    c_pris     = float(solde.conges_pris     if solde else 0)
    c_restants = float(solde.conges_restants if solde else 0)

    margin_x   = 1.0 * cm
    table_w    = width - 2 * margin_x   # ≈ 19 cm

    # ── helpers ──────────────────────────────────────────────────────────────
    def _fmt(v):
        if not v:
            return ''
        try:
            return f"{int(v):,}".replace(",", "\u202f")
        except Exception:
            return str(v)

    def _fmt0(v):
        if v is None:
            return ''
        if v == 0:
            return '0'
        try:
            return f"{int(v):,}".replace(",", "\u202f")
        except Exception:
            return str(v)

    # ════════════════════════════════════════════════════════════════════════
    # EN-TÊTE
    # ════════════════════════════════════════════════════════════════════════
    y = height - 0.8 * cm

    # Logo + raison sociale (gauche)
    logo_x, logo_y = margin_x, y - 2.0 * cm
    if entreprise and entreprise.logo:
        try:
            lp = entreprise.logo.path
            if os.path.exists(lp):
                p.drawImage(lp, logo_x, logo_y, width=3 * cm, height=2 * cm,
                            preserveAspectRatio=True)
        except Exception:
            pass
    nom_ent = entreprise.nom_entreprise if entreprise else "ENTREPRISE"
    p.setFont(_FONT_BOLD, 9)
    p.drawString(logo_x, logo_y - 0.45 * cm, nom_ent)

    # « BULLETIN DE PAIE » centré (légèrement à droite du logo)
    p.setFont(_FONT_BOLD, 16)
    p.drawCentredString(width / 2 + 1.5 * cm, y - 0.9 * cm, "BULLETIN DE PAIE")

    # Boîte info (haut droite)
    bx = width - 6.8 * cm
    by = y - 0.2 * cm
    bw = 6.2 * cm
    bh = 2.9 * cm
    p.setStrokeColor(colors.black)
    p.setLineWidth(0.5)
    p.rect(bx, by - bh, bw, bh)

    periode_debut = bulletin.periode.date_debut.strftime('%d/%m/%y') if bulletin.periode and bulletin.periode.date_debut else ''
    periode_fin   = bulletin.periode.date_fin.strftime('%d/%m/%y')   if bulletin.periode and bulletin.periode.date_fin   else ''
    date_pmt      = bulletin.date_calcul.strftime('%d/%m/%Y')         if bulletin.date_calcul else '-'

    box_lines = [
        ("Période du :", f"{periode_debut} au {periode_fin}"),
        ("Paiement",    date_pmt),
        ("Matricule :", str(emp.matricule or '-')),
        ("Ancienneté :", anciennete_str),
    ]
    iy = by - 0.55 * cm
    for lbl, val in box_lines:
        p.setFont(_FONT_BOLD, 7)
        p.drawString(bx + 0.25 * cm, iy, lbl)
        p.setFont(_FONT_NORMAL, 7)
        p.drawString(bx + 2.6 * cm, iy, val)
        iy -= 0.6 * cm

    y = logo_y - 0.9 * cm

    # Ligne séparatrice
    p.setLineWidth(1)
    p.line(margin_x, y, width - margin_x, y)
    y -= 0.45 * cm

    # ════════════════════════════════════════════════════════════════════════
    # INFORMATIONS EMPLOYÉ  (2 colonnes)
    # ════════════════════════════════════════════════════════════════════════
    left_col  = margin_x
    right_col = width / 2
    lbl_w     = 3.8 * cm

    def _emp_row(label, value, rlabel, rvalue, row_y):
        p.setFont(_FONT_BOLD, 7.5)
        p.drawString(left_col, row_y, label)
        p.setFont(_FONT_NORMAL, 7.5)
        p.drawString(left_col + lbl_w, row_y, str(value))
        if rlabel:
            p.setFont(_FONT_BOLD, 7.5)
            p.drawString(right_col, row_y, rlabel)
        if rvalue:
            p.setFont(_FONT_NORMAL if rlabel != "M." else _FONT_BOLD, 7.5)
            p.drawString(right_col + 2.5 * cm, row_y, str(rvalue))

    rows_emp = [
        ("N° de Sécurité Sociale", emp.num_cnss_individuel or '-', "",          ""),
        ("Indice",                 getattr(emp, 'indice', '')    or '-', "Niveau",   getattr(emp, 'niveau', '') or '-'),
        ("Coefficient",            getattr(emp, 'coefficient', '') or '-', "Horaire", getattr(emp, 'horaire', '') or '-'),
        ("Emploi",                 str(emp.poste or '-'),              "M.",       f"{emp.nom} {emp.prenoms}"),
        ("Qualification",          str(getattr(emp, 'qualification', '') or emp.poste or '-'), "", ""),
        ("Département",            str(emp.service or '-'),            "Adresse",  str(getattr(emp, 'adresse', '') or (entreprise.adresse if entreprise else '-'))),
    ]
    for i, (ll, lv, rl, rv) in enumerate(rows_emp):
        _emp_row(ll, lv, rl, rv, y - i * 0.42 * cm)
    y -= len(rows_emp) * 0.42 * cm + 0.25 * cm

    # ════════════════════════════════════════════════════════════════════════
    # TABLEAU CONGÉS
    # ════════════════════════════════════════════════════════════════════════
    conge_data = [
        ['Congé', 'Dates de congés', 'Repos Compensateur'],
        [f'Pris :      {c_pris:.3f}    Du      au', '', f'Pris :      0,000'],
        [f'Restant :  {c_restants:.3f}    Du      au', '', f'Restant :  0,000'],
        [f'Acquis :   {c_acquis:.3f}    Du      au', '', f'Acquis :   0,000'],
    ]
    cw_conge = [table_w * 0.46, table_w * 0.27, table_w * 0.27]
    ct = Table(conge_data, colWidths=cw_conge, rowHeights=11)
    ct.setStyle(TableStyle([
        ('FONTNAME',    (0, 0), (-1, 0),  _FONT_BOLD),
        ('FONTNAME',    (0, 1), (-1, -1), _FONT_NORMAL),
        ('FONTSIZE',    (0, 0), (-1, -1), 6.5),
        ('GRID',        (0, 0), (-1, -1), 0.3, colors.black),
        ('BACKGROUND',  (0, 0), (-1, 0),  colors.HexColor('#eeeeee')),
        ('ALIGN',       (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
    ]))
    ct_h = 4 * 11
    ct.wrapOn(p, width, height)
    ct.drawOn(p, margin_x, y - ct_h)
    y -= ct_h + 0.35 * cm

    # ════════════════════════════════════════════════════════════════════════
    # TABLEAU PRINCIPAL  (10 colonnes)
    # ════════════════════════════════════════════════════════════════════════
    # Colonnes : N° | Désignation | Nombre | Base | TxSal | GainSal | RetSal | TxPat | RetPat | Montant
    col_w = [0.55*cm, 4.1*cm, 1.05*cm, 1.95*cm, 0.85*cm, 2.0*cm, 2.0*cm, 0.85*cm, 2.0*cm, 3.6*cm]
    # total = 0.55+4.1+1.05+1.95+0.85+2.0+2.0+0.85+2.0+3.6 = 19.0 ✓

    # ── En-têtes 2 niveaux ──
    td = [
        ['N°', 'Désignation', 'Nombre', 'Base', 'Part Salariale', '', '', 'Part Patronale', '', 'Montant en GNF'],
        ['',   '',            '',       '',     'Taux', 'Gain', 'Retenue', 'Taux', 'Retenue', ''],
    ]

    # ── Gains ──
    num = 1
    for g in gains:
        nbre  = f"{g.nombre:g}" if g.nombre and g.nombre != 1 else ""
        base  = _fmt(g.base)  if g.base  else ""
        taux  = f"{g.taux}%"  if g.taux  else ""
        mnt   = _fmt0(g.montant)
        td.append([str(num), g.rubrique.libelle_rubrique[:32], nbre, base, taux, mnt, '', '', '', ''])
        num += 1

    # ── HS si non déjà dans gains ──
    hs_30   = float(getattr(bulletin, 'heures_supplementaires_30', 0) or 0)
    hs_60   = float(getattr(bulletin, 'heures_supplementaires_60', 0) or 0)
    prime_hs = float(getattr(bulletin, 'prime_heures_sup', 0) or 0)
    has_hs_in_gains = any('hs' in (g.rubrique.code_rubrique or '').lower() or
                          'heure' in (g.rubrique.libelle_rubrique or '').lower()
                          for g in gains)
    if not has_hs_in_gains:
        td.append([str(num), 'HS30%', f'{hs_30:g}h' if hs_30 else '', '', '', _fmt0(prime_hs) if hs_30 > 0 else '0', '', '', '', ''])
        num += 1
        _sal_h = Decimal(str(bulletin.salaire_base or 0)) / Decimal('173.33')
        mnt60  = int(_sal_h * Decimal(str(hs_60)) * Decimal('1.60')) if hs_60 > 0 else 0
        td.append([str(num), 'HS60%', f'{hs_60:g}h' if hs_60 else '', '', '', _fmt0(mnt60) if hs_60 > 0 else '0', '', '', '', ''])
        num += 1

    # ── Prime d'ancienneté (si absente des gains) ──
    has_anc = any('anciennet' in (g.rubrique.libelle_rubrique or '').lower() for g in gains)
    if not has_anc:
        td.append([str(num), "Prime d'ancienneté", '', '', '', '0', '', '', '', ''])
        num += 1

    # ── Manquant (retenue absence) ──
    absence = float(getattr(bulletin, 'retenue_absence', 0) or 0)
    td.append(['', 'Manquant', '', '', '', '', _fmt0(absence) if absence else '', '', '', ''])

    # ── Total brut ──
    td.append(['', 'Total brut', '', '', '', _fmt0(bulletin.salaire_brut), '', '', '', ''])

    # ── RTS ──
    base_rts = float(getattr(bulletin, 'base_rts', 0) or 0)
    taux_rts = float(getattr(bulletin, 'taux_effectif_rts', 0) or 0)
    td.append(['', 'RTS', '', _fmt(base_rts), f'{taux_rts:.1f}%' if taux_rts else '', '', _fmt0(bulletin.irg), '', '', ''])

    # ── Versement Forfaitaire ──
    vf    = float(getattr(bulletin, 'versement_forfaitaire', 0) or 0)
    td.append(['', 'Versement forfaitaire', '', '', '', '', '', '6%', _fmt0(vf), ''])

    # ── TA ou ONFPP ──
    ta    = float(getattr(bulletin, 'taxe_apprentissage', 0) or 0)
    onfpp = float(getattr(bulletin, 'contribution_onfpp', 0) or 0)
    if onfpp > 0:
        td.append(['', 'ONFPP', '', '', '', '', '', '1,5%', _fmt0(onfpp), ''])
    elif ta > 0:
        td.append(['', 'Taxe Apprentissage', '', '', '', '', '', '2%', _fmt0(ta), ''])

    # ── CNSS ──
    base_cnss = min(float(bulletin.salaire_brut), 2500000)
    td.append(['', 'CNSS', '', '', '5%', _fmt0(bulletin.cnss_employe), '', '18%', _fmt0(bulletin.cnss_employeur), ''])

    # ── Total cotisation ──
    tot_sal = float(bulletin.cnss_employe) + float(bulletin.irg)
    tot_pat = vf + ta + onfpp + float(bulletin.cnss_employeur)
    td.append(['', 'Total cotisation', '', '', '', _fmt0(tot_sal), '', '', _fmt0(tot_pat), ''])

    RH = 12   # row height (pt)
    nb = len(td)

    main_t = Table(td, colWidths=col_w, rowHeights=RH)

    # ── Index des lignes spéciales ──
    idx_brut = next((i for i, r in enumerate(td) if r[1] == 'Total brut'), None)
    idx_cot  = next((i for i, r in enumerate(td) if r[1] == 'Total cotisation'), None)

    ts = [
        # En-tête fond gris clair
        ('BACKGROUND',    (0, 0), (-1, 1),  colors.HexColor('#eeeeee')),
        ('FONTNAME',      (0, 0), (-1, 1),  _FONT_BOLD),
        ('FONTSIZE',      (0, 0), (-1, -1), 7),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN',         (1, 2), (1, -1),  'LEFT'),   # Désignation
        ('ALIGN',         (3, 2), (-1, -1), 'RIGHT'),  # colonnes numériques
        ('GRID',          (0, 0), (-1, -1), 0.35, colors.black),
        ('LEFTPADDING',   (0, 0), (-1, -1), 2),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 2),
        # Spans en-tête
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (1, 0), (1, 1)),
        ('SPAN', (2, 0), (2, 1)),
        ('SPAN', (3, 0), (3, 1)),
        ('SPAN', (4, 0), (6, 0)),   # Part Salariale
        ('SPAN', (7, 0), (8, 0)),   # Part Patronale
        ('SPAN', (9, 0), (9, 1)),
    ]
    if idx_brut is not None:
        ts += [('FONTNAME',   (0, idx_brut), (-1, idx_brut), _FONT_BOLD),
               ('BACKGROUND', (0, idx_brut), (-1, idx_brut), colors.HexColor('#f0f0f0'))]
    if idx_cot is not None:
        ts += [('FONTNAME',   (0, idx_cot),  (-1, idx_cot),  _FONT_BOLD),
               ('BACKGROUND', (0, idx_cot),  (-1, idx_cot),  colors.HexColor('#f0f0f0'))]

    main_t.setStyle(TableStyle(ts))
    mt_h = nb * RH
    main_t.wrapOn(p, width, height)
    main_t.drawOn(p, margin_x, y - mt_h)
    y -= mt_h + 0.4 * cm

    # ════════════════════════════════════════════════════════════════════════
    # PIED RÉCAPITULATIF
    # ════════════════════════════════════════════════════════════════════════
    charge_sal = float(bulletin.cnss_employe) + float(bulletin.irg)
    charge_pat = vf + ta + onfpp + float(bulletin.cnss_employeur)
    avnat      = float(getattr(bulletin, 'avantage_nature', 0) or 0)
    net_imp    = float(getattr(bulletin, 'base_rts', 0) or 0)

    per_str  = bulletin.periode.date_debut.strftime('%d/%m/%y') if bulletin.periode and bulletin.periode.date_debut else ''
    ann_str  = str(bulletin.annee_paie)

    # Colonnes pied (total ≈ 14.5 cm, Net à payer dans boîte séparée)
    fc_w = [2.3*cm, 1.4*cm, 2.5*cm, 2.1*cm, 2.2*cm, 1.9*cm, 2.1*cm]
    fc_total = sum(fc_w)   # 14.5 cm

    fd = [
        ['Période', 'Année', 'S.Brut', 'Charge\nSalariale', 'Charge\nPatronale', 'Avan. En\nnature', 'Net\nImposable'],
        [per_str,   ann_str, _fmt0(bulletin.salaire_brut), _fmt0(charge_sal),
         _fmt0(charge_pat), f"{avnat:.2f}", _fmt0(net_imp)],
    ]
    ft = Table(fd, colWidths=fc_w, rowHeights=15)
    ft.setStyle(TableStyle([
        ('FONTNAME',    (0, 0), (-1, 0),  _FONT_BOLD),
        ('FONTNAME',    (0, 1), (-1, 1),  _FONT_NORMAL),
        ('FONTSIZE',    (0, 0), (-1, -1), 7),
        ('GRID',        (0, 0), (-1, -1), 0.4, colors.black),
        ('ALIGN',       (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND',  (0, 0), (-1, 0),  colors.HexColor('#eeeeee')),
    ]))
    ft_h = 2 * 15
    ft.wrapOn(p, width, height)
    ft.drawOn(p, margin_x, y - ft_h)

    # Boîte « Net à payer » (droite du pied)
    nb_x = margin_x + fc_total + 0.3 * cm
    nb_w = table_w - fc_total - 0.3 * cm
    p.setStrokeColor(colors.black)
    p.setLineWidth(1.2)
    p.setFillColor(colors.white)
    p.rect(nb_x, y - ft_h, nb_w, ft_h, stroke=1, fill=1)
    p.setFillColor(colors.black)
    p.setFont(_FONT_BOLD, 8)
    p.drawCentredString(nb_x + nb_w / 2, y - 0.55 * cm, "Net à payer")
    p.setFont(_FONT_BOLD, 10)
    net_str = f"{int(bulletin.net_a_payer):,} GNF".replace(",", "\u202f")
    p.drawCentredString(nb_x + nb_w / 2, y - 1.15 * cm, net_str)
    y -= ft_h + 0.5 * cm

    # ════════════════════════════════════════════════════════════════════════
    # SIGNATURES
    # ════════════════════════════════════════════════════════════════════════
    y -= 0.5 * cm
    p.setFont(_FONT_BOLD, 8)
    p.drawString(margin_x + 1 * cm, y, "Employeur")
    p.drawString(width - 5.5 * cm, y, "Employé(e)")
    y -= 0.3 * cm
    p.setFont(_FONT_NORMAL, 7)
    if entreprise:
        p.drawString(margin_x + 1 * cm, y, nom_ent)
    p.drawString(width - 5.5 * cm, y, f"{emp.nom} {emp.prenoms}")
    y -= 1.4 * cm
    p.setDash(3, 3)
    p.line(margin_x, y, margin_x + 5 * cm, y)
    p.line(width - 6 * cm, y, width - margin_x, y)
    p.setDash()

    # ════════════════════════════════════════════════════════════════════════
    # PIED DE PAGE
    # ════════════════════════════════════════════════════════════════════════
    p.setFont(_FONT_NORMAL, 6)
    p.drawCentredString(width / 2, 1.5 * cm, "Ce bulletin est conforme à la législation guinéenne en vigueur.")
    if entreprise:
        p.drawCentredString(width / 2, 1.1 * cm,
            f"{nom_ent} — {entreprise.adresse or ''} — Tél: {entreprise.telephone or ''}")
    p.drawCentredString(width / 2, 0.7 * cm,
        f"Document généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')}")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.read()

