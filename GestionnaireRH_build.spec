# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file pour GestionnaireRH
Génère un exécutable Windows standalone avec icône
"""

import os
import sys
from pathlib import Path

# Répertoire du projet
PROJECT_DIR = Path(r'C:\Users\LENO\Desktop\GestionnaireRHofline')

block_cipher = None

# Collecter tous les fichiers de données
datas = [
    # Templates Django
    (str(PROJECT_DIR / 'templates'), 'templates'),
    # Fichiers statiques
    (str(PROJECT_DIR / 'static'), 'static'),
    (str(PROJECT_DIR / 'staticfiles'), 'staticfiles'),
    # Applications Django
    (str(PROJECT_DIR / 'core'), 'core'),
    (str(PROJECT_DIR / 'employes'), 'employes'),
    (str(PROJECT_DIR / 'paie'), 'paie'),
    (str(PROJECT_DIR / 'temps_travail'), 'temps_travail'),
    (str(PROJECT_DIR / 'recrutement'), 'recrutement'),
    (str(PROJECT_DIR / 'formation'), 'formation'),
    (str(PROJECT_DIR / 'dashboard'), 'dashboard'),
    (str(PROJECT_DIR / 'payments'), 'payments'),
    (str(PROJECT_DIR / 'conges'), 'conges'),
    (str(PROJECT_DIR / 'contrats'), 'contrats'),
    (str(PROJECT_DIR / 'portail'), 'portail'),
    (str(PROJECT_DIR / 'comptabilite'), 'comptabilite'),
    # Configuration Django
    (str(PROJECT_DIR / 'gestionnaire_rh'), 'gestionnaire_rh'),
    # Fichiers de configuration
    (str(PROJECT_DIR / 'manage.py'), '.'),
]

# Modules cachés nécessaires pour Django
hiddenimports = [
    'django',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.template.backends.django',
    'django.template.loader_tags',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_filters',
    'widget_tweaks',
    'import_export',
    'rest_framework',
    'corsheaders',
    'corsheaders.middleware',
    'axes',
    'axes.middleware',
    'csp',
    'csp.middleware',
    'whitenoise',
    'whitenoise.middleware',
    'whitenoise.storage',
    'reportlab',
    'reportlab.lib',
    'reportlab.pdfgen',
    'reportlab.platypus',
    'reportlab.graphics',
    'openpyxl',
    'PIL',
    'decouple',
    'core',
    'core.models',
    'core.views',
    'core.middleware',
    'core.middleware_licence',
    'employes',
    'employes.models',
    'employes.views',
    'paie',
    'paie.models',
    'paie.views',
    'paie.services',
    'temps_travail',
    'temps_travail.models',
    'temps_travail.views',
    'recrutement',
    'recrutement.models',
    'recrutement.views',
    'formation',
    'formation.models',
    'formation.views',
    'dashboard',
    'dashboard.views',
    'payments',
    'payments.models',
    'payments.views',
    'conges',
    'conges.models',
    'conges.views',
    'contrats',
    'contrats.models',
    'contrats.views',
    'portail',
    'portail.views',
    'comptabilite',
    'comptabilite.models',
    'comptabilite.views',
    'gestionnaire_rh.settings',
    'gestionnaire_rh.settings_portable',
    'gestionnaire_rh.urls',
    'gestionnaire_rh.wsgi',
    # Tkinter (fenetre d'activation de licence)
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    '_tkinter',
    # Stdlib
    'winreg',
    'hmac',
    'hashlib',
    'base64',
    'uuid',
    'socket',
    'platform',
]

a = Analysis(
    [str(PROJECT_DIR / 'run_server.py')],
    pathex=[str(PROJECT_DIR)],
    binaries=[
        # Nuitka-compiled license module (native binary — non-decompilable)
        (str(PROJECT_DIR / 'dist_nuitka' / 'license_manager.cp313-win_amd64.pyd'), '.'),
    ],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
        'license_manager',   # excluded: native .pyd is in binaries instead
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=2,   # strip docstrings + assert statements
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GestionnaireRH',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # True pour voir les logs, False pour mode silencieux
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(PROJECT_DIR / 'static' / 'img' / 'logo.ico') if (PROJECT_DIR / 'static' / 'img' / 'logo.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GestionnaireRH',
)

# ─── Post-build: remove license_manager.py source, keep only the .pyd ─────────
import shutil as _shutil, os as _os
_internal = str(PROJECT_DIR / 'dist' / 'GestionnaireRH' / '_internal')
_py_src = _os.path.join(_internal, 'license_manager.py')
_pyc_dir = _os.path.join(_internal, '__pycache__')
_pyd_src = str(PROJECT_DIR / 'dist_nuitka' / 'license_manager.cp313-win_amd64.pyd')
_pyd_dst = _os.path.join(_internal, 'license_manager.cp313-win_amd64.pyd')

if _os.path.exists(_py_src):
    _os.remove(_py_src)
    print('[Protection] Removed license_manager.py from dist')
if _os.path.exists(_pyc_dir):
    for _f in _os.listdir(_pyc_dir):
        if 'license_manager' in _f:
            _os.remove(_os.path.join(_pyc_dir, _f))
if _os.path.exists(_pyd_src) and not _os.path.exists(_pyd_dst):
    _shutil.copy2(_pyd_src, _pyd_dst)
    print('[Protection] Installed license_manager.pyd in dist')
print('[Protection] license_manager protection applied.')
