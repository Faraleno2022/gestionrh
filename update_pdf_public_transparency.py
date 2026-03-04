#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to add transparency fields to public PDF"""

# Lire le fichier
with open('paie/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ===========================================
# Mise à jour PDF Public: Section RÉCAPITULATIF
# ===========================================

# Trouver la deuxième occurrence de RÉCAPITULATIF (dans telecharger_bulletin_public)
old_recap_public = '''    # === RÉCAPITULATIF ===
    rappel = getattr(bulletin, 'rappel_salaire', 0) or 0
    trop_percu = getattr(bulletin, 'retenue_trop_percu', 0) or 0
    has_rappel = rappel > 0
    has_trop_percu = trop_percu > 0
    extra_lines = (1 if has_rappel else 0) + (1 if has_trop_percu else 0)
    recap_height = 2.1*cm + extra_lines * 0.4*cm'''

new_recap_public = '''    # === RÉCAPITULATIF ===
    rappel = getattr(bulletin, 'rappel_salaire', 0) or 0
    trop_percu = getattr(bulletin, 'retenue_trop_percu', 0) or 0
    has_rappel = rappel > 0
    has_trop_percu = trop_percu > 0
    abatt_forfait = getattr(bulletin, 'abattement_forfaitaire', 0) or 0
    has_abatt = abatt_forfait > 0
    extra_lines = (1 if has_rappel else 0) + (1 if has_trop_percu else 0) + (1 if has_abatt else 0)
    recap_height = 2.1*cm + extra_lines * 0.35*cm'''

# Trouver la deuxième occurrence (après 'gains_table.drawOn')
if 'gains_table.drawOn' in content:
    idx_gains = content.find('gains_table.drawOn')
    idx_start = content.find(old_recap_public, idx_gains)
    if idx_start != -1:
        content = content[:idx_start] + new_recap_public + content[idx_start + len(old_recap_public):]
        print('✓ Section RÉCAPITULATIF calc (PDF Public)')

# Mise à jour de l'affichage offset dans PDF Public
old_offset_public = '''    offset_y = 1*cm
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

new_offset_public = '''    offset_y = 1*cm
    
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

# Remplacer dans PDF Public
offset_count = content.count(old_offset_public)
if offset_count >= 2:
    # Remplacer la 2ème occurrence
    idx_first = content.find(old_offset_public)
    idx_second_start = content.find(old_offset_public, idx_first + 1)
    if idx_second_start != -1:
        content = content[:idx_second_start] + new_offset_public + content[idx_second_start + len(old_offset_public):]
        print('✓ Affichage offset details (PDF Public)')

# CHARGES PATRONALES du PDF Public
old_charges_public = '''    # === CHARGES PATRONALES ===
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

new_charges_public = '''    # === CHARGES PATRONALES ===
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

# Trouver la 2ème occurrence (dans PDF Public)
occurrences = content.count(old_charges_public)
if occurrences >= 2:
    idx_first_charges = content.find(old_charges_public)
    idx_second_charges = content.find(old_charges_public, idx_first_charges + 1)
    if idx_second_charges != -1:
        content = content[:idx_second_charges] + new_charges_public + content[idx_second_charges + len(old_charges_public):]
        print('✓ Section CHARGES PATRONALES (PDF Public)')
elif occurrences == 1:
    content = content.replace(old_charges_public, new_charges_public, 1)
    print('✓ Section CHARGES PATRONALES (seule occurrence trouvée)')

# Écrire le fichier
with open('paie/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('\n✅ Mise à jour du PDF Public complétée!')
