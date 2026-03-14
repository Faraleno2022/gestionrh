import os, re

templates_dir = 'templates'
results_missing = []
results_ok = []
all_templates = []

for root, dirs, files in os.walk(templates_dir):
    for f in files:
        if f.endswith('.html'):
            fpath = os.path.join(root, f).replace('\\', '/')
            all_templates.append(fpath)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                    content = fh.read()
            except:
                continue
            form_pattern = re.compile(r'<form[^>]*>', re.IGNORECASE)
            form_end_pattern = re.compile(r'</form>', re.IGNORECASE)
            form_starts = [(m.start(), m.group()) for m in form_pattern.finditer(content)]
            form_ends = [m.start() for m in form_end_pattern.finditer(content)]
            if not form_starts:
                continue
            for i, (fstart, ftag) in enumerate(form_starts):
                matching_end = None
                for fe in form_ends:
                    if fe > fstart:
                        matching_end = fe
                        break
                if matching_end is None:
                    matching_end = len(content)
                form_section = content[fstart:matching_end]
                line_num = content[:fstart].count('\n') + 1
                has_submit = bool(re.search(r'type=.submit.', form_section, re.IGNORECASE))
                is_get = 'method=' in ftag.lower() and 'get' in ftag.lower()
                is_hidden = 'display: none' in ftag or 'display:none' in ftag
                has_js = bool(re.search(r'\.submit\(\)', form_section))
                note = ''
                if is_get: note += '[GET]'
                if is_hidden: note += '[HIDDEN]'
                if has_js: note += '[JS]'
                if has_submit:
                    results_ok.append((fpath, line_num))
                else:
                    results_missing.append((fpath, line_num, ftag.strip()[:90], note))

print("=" * 80)
print("FORMS WITHOUT SUBMIT BUTTONS:")
print("=" * 80)
for fpath, line, tag, note in sorted(results_missing):
    print(f"  {fpath}:{line} {note}")
print()
print(f"Missing: {len(results_missing)}, OK: {len(results_ok)}, Templates: {len(all_templates)}")
print()
print("=" * 80)
print("ALL TEMPLATE FILES:")
print("=" * 80)
for t in sorted(all_templates):
    print(f"  {t}")
