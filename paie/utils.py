"""
Utilitaires de paie - Génération PDF de bulletins
"""
import io
import os
from decimal import Decimal
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from django.utils import timezone


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
    y -= 0.35*cm
    # Dates de la période
    p.setFont("Helvetica", 8)
    periode_detail = f"Du {bulletin.periode.date_debut.strftime('%d/%m/%Y')} au {bulletin.periode.date_fin.strftime('%d/%m/%Y')}" if bulletin.periode.date_debut and bulletin.periode.date_fin else ""
    p.drawCentredString(width/2, y, periode_detail)
    y -= 0.6*cm
    
    # === INFORMATIONS EMPLOYÉ ===
    p.setFillColor(colors.HexColor("#ce1126"))
    p.setFont("Helvetica-Bold", 9)
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
        ["Solde congés:", f"{conges_restants:g} j", "", ""],
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
    rappel = getattr(bulletin, 'rappel_salaire', 0) or 0
    trop_percu = getattr(bulletin, 'retenue_trop_percu', 0) or 0
    has_rappel = rappel > 0
    has_trop_percu = trop_percu > 0
    extra_lines = (1 if has_rappel else 0) + (1 if has_trop_percu else 0)
    recap_height = 2.1*cm + extra_lines * 0.4*cm
    p.setStrokeColor(colors.HexColor("#ce1126"))
    p.setLineWidth(2)
    p.rect(1.5*cm, y - recap_height, width - 3*cm, recap_height, stroke=1, fill=0)
    
    p.setFont("Helvetica-Bold", 10)
    p.setFillColor(colors.black)
    p.drawString(2*cm, y - 0.5*cm, "SALAIRE BRUT:")
    p.drawRightString(width - 2*cm, y - 0.5*cm, f"{bulletin.salaire_brut:,.0f} GNF".replace(",", " "))
    
    # CNSS et RTS alignés sur la même ligne
    p.setFont("Helvetica", 8)
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
    p.setFont("Helvetica-Bold", 11)
    p.drawString(2*cm, y - offset_y - 0.7*cm, "NET À PAYER:")
    p.drawRightString(width - 2*cm, y - offset_y - 0.7*cm, f"{bulletin.net_a_payer:,.0f} GNF".replace(",", " "))
    p.setFillColor(colors.black)
    
    y -= recap_height + 0.5*cm
    
    # === CHARGES PATRONALES ===
    vf = getattr(bulletin, 'versement_forfaitaire', 0) or 0
    ta = getattr(bulletin, 'taxe_apprentissage', 0) or 0
    onfpp = getattr(bulletin, 'contribution_onfpp', 0) or 0
    total_charges = bulletin.cnss_employeur + vf + ta + onfpp
    
    # Ligne titre + détail alignés sur une seule ligne
    p.setFont("Helvetica-Bold", 8)
    p.drawString(1.5*cm, y, "CHARGES PATRONALES:")
    y -= 0.35*cm
    p.setFont("Helvetica", 7)
    # Toutes les cotisations patronales sur la même ligne
    col1 = f"CNSS 18%: {bulletin.cnss_employeur:,.0f}".replace(",", " ")
    col2 = f"VF 6%: {vf:,.0f}".replace(",", " ")
    if ta > 0:
        col3 = f"TA 1,5%: {ta:,.0f}".replace(",", " ")
    elif onfpp > 0:
        col3 = f"ONFPP 1,5%: {onfpp:,.0f}".replace(",", " ")
    else:
        col3 = ""
    p.drawString(1.5*cm, y, col1)
    p.drawString(6.5*cm, y, col2)
    if col3:
        p.drawString(11*cm, y, col3)
    p.setFont("Helvetica-Bold", 8)
    p.drawRightString(width - 1.5*cm, y, f"Total: {total_charges:,.0f} GNF".replace(",", " "))
    y -= 0.3*cm
    
    # === ZONE DE SIGNATURES ===
    y -= 1.2*cm
    p.setFont("Helvetica-Bold", 8)
    p.drawString(2*cm, y, "L'Employeur")
    p.drawString(12*cm, y, "L'Employé(e)")
    y -= 0.4*cm
    p.setFont("Helvetica", 7)
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
    p.setFont("Helvetica", 6)
    p.drawCentredString(4.5*cm, y, "Date et signature")
    p.drawCentredString(14.5*cm, y, "Lu et approuvé, date et signature")
    
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
    
    buffer.seek(0)
    return buffer.read()
