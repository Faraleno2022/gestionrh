#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fix spacing in PDF generation for bulletin de paie"""

import re

# Read the file
with open('paie/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the two occurrences of "y -= table_height + 0.4*cm" after retenues_table.drawOn
# We need to replace the exact line that comes after "retenues_table.drawOn(p, 1.5*cm, y - table_height)"
# and before "# === DÉTAIL CALCUL RTS"

# Count replacements
count = 0

# This pattern looks for the exact sequence we want to replace
pattern = r'(retenues_table\.drawOn\(p, 1\.5\*cm, y - table_height\))\n(\s+)y \-= table_height \+ 0\.4\*cm'
replacement = r'\1\n\2y -= table_height + 0.5*cm'

new_content = re.sub(pattern, replacement, content)

if new_content != content:
    # Count how many replacements were made
    count = len(re.findall(pattern, content))
    print(f"Found and replaced {count} occurrences")
    
    # Write back to file
    with open('paie/views.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("File updated successfully!")
else:
    print("No replacements made - pattern not found")
