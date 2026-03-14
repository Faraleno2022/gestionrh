import os, re
from pathlib import Path

base = Path('.')
results = []

# Exclusions
excluded_files = [
    'employes/form.html',
    'employes/contrat_form.html',
]

# Find all HTML templates
template_dirs = [Path('templates'), Path('formation/templates'), Path('comptabilite/templates')]
html_files = []
for td in template_dirs:
    if td.exists():
        for f in td.rglob('*.html'):
            html_files.append(f)

for fpath in sorted(html_files):
    rel = str(fpath).replace('\\', '/')
    skip = False
    for excl in excluded_files:
        if excl in rel:
            skip = True
            break
    if skip:
        continue

    try:
        content = fpath.read_text(encoding='utf-8', errors='replace')
    except:
        continue
    
    lines = content.split('\n')
    
    form_pattern = re.compile(r'<form[^>]*method=["\']post["\'][^>]*>', re.IGNORECASE)
    
    i = 0
    while i < len(lines):
        match = form_pattern.search(lines[i])
        if match:
            form_start_line = i + 1  # 1-based
            form_tag = match.group(0)
            
            # Find the closing </form>
            form_content = ''
            form_end_line = None
            for j in range(i, min(i + 200, len(lines))):
                form_content += lines[j] + '\n'
                if '</form>' in lines[j].lower():
                    form_end_line = j + 1  # 1-based
                    break
            
            if form_end_line is None:
                i += 1
                continue
            
            # Check exclusions
            # 1. Modal form
            context_before = '\n'.join(lines[max(0, i-15):i]).lower()
            is_modal = 'modal' in context_before
            
            # 2. Hidden form
            is_hidden = 'display: none' in form_tag.lower() or 'display:none' in form_tag.lower()
            
            # 3. Inline action forms (display: inline - usually delete buttons in tables)
            is_inline_action = 'display: inline' in form_tag.lower() or 'display:inline' in form_tag.lower()
            
            # 4. Check form content
            form_inner = form_content
            inner_clean = re.sub(r'\{%\s*csrf_token\s*%\}', '', form_inner)
            inner_clean = re.sub(r'</?form[^>]*>', '', inner_clean)
            
            has_visible_fields = bool(re.search(r'<(input|select|textarea)', inner_clean, re.IGNORECASE))
            has_django_form = bool(re.search(r'\{\{.*form', inner_clean, re.IGNORECASE))
            
            # Check for submit mechanisms
            has_submit_type = bool(re.search(r'type=["\']submit["\']', form_content, re.IGNORECASE))
            has_any_button = bool(re.search(r'<button', form_content, re.IGNORECASE))
            has_js_submit = bool(re.search(r'\.submit\(\)', content))  # Check whole file for JS submit
            has_btn_link = bool(re.search(r'btn.*enregistrer|btn.*sauvegarder|btn.*valider|btn.*soumettre|btn.*confirmer|btn.*envoyer|btn.*calculer', form_content, re.IGNORECASE))
            
            # Skip modals
            if is_modal:
                i = form_end_line
                continue
            
            # Skip hidden forms
            if is_hidden:
                i = form_end_line
                continue
            
            # Skip inline action forms
            if is_inline_action:
                i = form_end_line
                continue
            
            # Determine if form has fields
            has_fields = has_visible_fields or has_django_form
            
            # If no fields and no submit, it might be intentional (csrf-only)
            if not has_fields and not has_submit_type and not has_any_button:
                i = form_end_line
                continue
            
            # Check: has fields but NO submit button
            missing_submit = False
            reason = ''
            if has_fields and not has_submit_type:
                if has_any_button:
                    # Has a button but not type=submit - check what type
                    # In HTML, <button> without type defaults to submit, so this is OK
                    # But <button type="button"> is NOT a submit
                    button_types = re.findall(r'<button[^>]*type=["\'](\w+)["\']', form_content, re.IGNORECASE)
                    buttons_no_type = len(re.findall(r'<button(?![^>]*type=)', form_content, re.IGNORECASE))
                    if buttons_no_type > 0:
                        pass  # default button type is submit, OK
                    elif all(t.lower() != 'submit' for t in button_types):
                        missing_submit = True
                        reason = 'has button(s) but none are type=submit: [' + ','.join(button_types) + ']'
                else:
                    missing_submit = True
                    reason = 'no button element at all'
            
            if missing_submit:
                action_match = re.search(r'action=["\']([^"\']*)["\']', form_tag)
                action = action_match.group(1) if action_match else '(same page)'
                
                field_preview = []
                for ln in form_content.split('\n'):
                    stripped = ln.strip()
                    if re.search(r'(form\.|form |label|<input|<select|<textarea)', stripped, re.IGNORECASE):
                        field_preview.append(stripped[:100])
                    if len(field_preview) >= 3:
                        break
                snippet = ' | '.join(field_preview) if field_preview else '(django form rendering)'
                
                results.append({
                    'file': str(fpath).replace('\\', '/'),
                    'line': form_start_line,
                    'end': form_end_line,
                    'action': action,
                    'snippet': snippet[:200],
                    'has_js': has_js_submit,
                    'reason': reason,
                })
            
            i = form_end_line if form_end_line else i + 1
        else:
            i += 1

print('=== Found ' + str(len(results)) + ' POST forms potentially missing submit buttons ===')
print()
for r in results:
    print('FILE: ' + r['file'])
    print('  Lines: ' + str(r['line']) + '-' + str(r['end']))
    print('  Action: ' + r['action'])
    print('  Fields: ' + r['snippet'])
    if r['has_js']:
        print('  NOTE: File has .submit() JS call - may be submitted via JavaScript')
    print('  Reason: ' + r['reason'])
    print()
