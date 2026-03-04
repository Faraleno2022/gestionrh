#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to add compliance transparency fields to PDF generation"""

import re

# Lire le fichier
with open('paie/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ===========================================
# Mise à jour 1: Section RÉCAPITULATIF (calcul de recap_height)
# ===========================================
old_recap_calc = '''    # === RÉCAPITULATIF ===
    rappel = getattr(bulletin, 'rappel_salaire', 0) or 0
    trop_percu = getattr(bulletin, 'retenue_trop_percu', 0) or 0
    has_rappel = rappel > 0
    has_trop_percu = trop_percu > 0
    extra_lines = (1 if has_rappel else 0) + (1 if has_trop_percu else 0)
    recap_height = 2.1*cm + extra_lines * 0.4*cm'''

new_recap_calc = '''    # === RÉCAPITULATIF ===
    rappel = getattr(bulletin, 'rappel_salaire', 0) or 0
    trop_percu = getattr(bulletin, 'retenue_trop_percu', 0) or 0
    has_rappel = rappel > 0
    has_trop_percu = trop_percu > 0
    abatt_forfait = getattr(bulletin, 'abattement_forfaitaire', 0) or 0
    has_abatt = abatt_forfait > 0
    extra_lines = (1 if has_rappel else 0) + (1 if has_trop_percu else 0) + (1 if has_abatt else 0)
    recap_height = 2.1*cm + extra_lines * 0.35*cm'''

# Trouver et remplacer dans telecharger_bulletin_pdf (avant rts_table.drawOn)
idx_rts = content.find('rts_table.drawOn')
if idx_rts != -1:
    idx_start = content.rfind(old_recap_calc, 0, idx_rts)
    if idx_start != -1:
        content = content[:idx_start] + new_recap_calc + content[idx_start + len(old_recap_calc):]
        print('✓ Section RÉCAPITULATIF calc (PDF 1)')

# ===========================================
# Mise à jour 2: Affichage des détails dans RÉCAPITULATIF
# ===========================================
old_offset = '''    offset_y = 1*cm
    if has_rappel:
        offset_y += 0.4*cm
        p.setFillColor(colors.HexColor("#007bff"))
        p.drawString(2*cm, y - offset_y, "Rappel/Complément salaire précédent:")
        p.drawRightString(width - 2*cm, y - offset_y, f"+ {rappel:,.0f} GNF".replace(",", " "))
    if has_trop_percu:
        offset_y += 0.4*cm
        p.setFillColor(colors.HexColor("#dc3545"))
        p.drawString(2*cm, y - offset_y, "Retenue trop-perçu salaire précédent:")
        p.drawRightString(width - 2*cm, y - offset_y, f"- {trop_percu:,.0f} GNF".replace(",", " "))'''

new_offset = '''    offset_y = 1*cm
    
    # Afficher l'abattement forfaitaire si présent (détail RTS)
    if has_abatt:
        offset_y += 0.35*cm
        p.setFont("Helvetica", 7)
        p.setFillColor(colors.HexColor("#666666"))
        p.drawString(2.3*cm, y - offset_y, f"└─ abattement 25%: {abatt_forfait:,.0f}".replace(",", " "))
    
    if has_rappel:
        offset_y += 0.35*cm
        p.setFillColor(colors.HexColor("#007bff"))
        p.setFont("Helvetica", 8)
        p.drawString(2*cm, y - offset_y, "Rappel/Complément salaire précédent:")
        p.drawRightString(width - 2*cm, y - offset_y, f"+ {rappel:,.0f} GNF".replace(",", " "))
    if has_trop_percu:
        offset_y += 0.35*cm
        p.setFillColor(colors.HexColor("#dc3545"))
        p.setFont("Helvetica", 8)
        p.drawString(2*cm, y - offset_y, "Retenue trop-perçu salaire précédent:")
        p.drawRightString(width - 2*cm, y - offset_y, f"- {trop_percu:,.0f} GNF".replace(",", " "))'''

# Remplacer dans telecharger_bulletin_pdf
idx_rts2 = content.find('rts_table.drawOn')
if idx_rts2 != -1:
    idx_start2 = content.rfind(old_offset, 0, idx_rts2 + 1000)
    if idx_start2 != -1:
        content = content[:idx_start2] + new_offset + content[idx_start2 + len(old_offset):]
        print('✓ Affichage offset details (PDF 1)')

# ===========================================
# Mise à jour 3: Section CHARGES PATRONALES
# ===========================================
old_charges = '''    # === CHARGES PATRONALES ===
    vf = getattr(bulletin, 'versement_forfaitaire', 0) or 0
    ta = getattr(bulletin, 'taxe_apprentissage', 0) or 0
    onfpp = getattr(bulletin, 'contribution_onfpp', 0) or 0
    total_charges = bulletin.cnss_employeur + vf + ta + onfpp
    
    p.setFont("Helvetica-Bold", 8)
    p.drawString(1.5*cm, y, "CHARGES PATRONALES:")
    y -= 0.35*cm
    p.setFont("Helvetica", 6.5)
    p.drawString(1.5*cm, y, f"CNSS 18%: {bulletin.cnss_employeur:,.0f}".replace(",", " "))
    p.drawString(5.5*cm, y, f"VF 6%: {vf:,.0f}".replace(",", " "))
    p.drawString(9*cm, y, f"TA 1,5%: {ta:,.0f}".replace(",", " "))
    p.drawString(12.5*cm, y, f"ONFPP 1,5%: {onfpp:,.0f}".replace(",", " "))
    p.setFont("Helvetica-Bold", 7)
    p.drawRightString(width - 1.5*cm, y, f"Total: {total_charges:,.0f} GNF".replace(",", " "))
    y -= 0.3*cm'''

new_charges = '''    # === CHARGES PATRONALES ===
    vf = getattr(bulletin, 'versement_forfaitaire', 0) or 0
    ta = getattr(bulletin, 'taxe_apprentissage', 0) or 0
    onfpp = getattr(bulletin, 'contribution_onfpp', 0) or 0
    base_vf = getattr(bulletin, 'base_vf', 0) or 0
    nb_sal = getattr(bulletin, 'nombre_salaries', 0) or 0
    total_charges = bulletin.cnss_employeur + vf + ta + onfpp
    
    p.setFont("Helvetica-Bold", 8)
    p.drawString(1.5*cm, y, "CHARGES PATRONALES:")
    y -= 0.35*cm
    p.setFont("Helvetica", 6.5)
    p.drawString(1.5*cm, y, f"CNSS 18%: {bulletin.cnss_employeur:,.0f}".replace(",", " "))
    p.drawString(5.5*cm, y, f"VF 6%: {vf:,.0f}".replace(",", " "))
    # TA ou ONFPP selon effectif
    if ta > 0:
        p.drawString(9*cm, y, f"TA 2% (eff: {nb_sal} <30): {ta:,.0f}".replace(",", " "))
    elif onfpp > 0:
        p.drawString(9*cm, y, f"ONFPP 1,5% (eff: {nb_sal} ≥30): {onfpp:,.0f}".replace(",", " "))
    p.setFont("Helvetica-Bold", 7)
    p.drawRightString(width - 1.5*cm, y, f"Total: {total_charges:,.0f} GNF".replace(",", " "))
    y -= 0.3*cm
    # Base de calcul VF si présente
    if base_vf > 0:
        p.setFont("Helvetica", 6)
        p.setFillColor(colors.HexColor("#666666"))
        p.drawString(1.5*cm, y, f"└─ base calc VF: {base_vf:,.0f}".replace(",", " "))
        y -= 0.25*cm
    p.setFillColor(colors.black)'''

if old_charges in content:
    content = content.replace(old_charges, new_charges, 1)
    print('✓ Section CHARGES PATRONALES (PDF 1)')

# Écrire le fichier
with open('paie/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('\n✅ Mise à jour du PDF complétée!')
