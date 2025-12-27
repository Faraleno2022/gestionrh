#!/usr/bin/env python
"""
Script de construction de l'installateur Windows pour GestionnaireRH.
Ce script:
1. Collecte les fichiers statiques Django
2. Crée l'exécutable avec PyInstaller
3. Génère l'installateur avec Inno Setup (si disponible)
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

# Configuration
PROJECT_DIR = Path(__file__).parent.parent
INSTALLER_DIR = PROJECT_DIR / 'installer'
DIST_DIR = INSTALLER_DIR / 'dist'
BUILD_DIR = INSTALLER_DIR / 'build'

def run_command(cmd, cwd=None):
    """Exécute une commande et affiche la sortie."""
    print(f"\n>>> {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=False)
    return result.returncode == 0

def clean_build():
    """Nettoie les dossiers de build précédents."""
    print("\n[1/6] Nettoyage des builds précédents...")
    for folder in [DIST_DIR, BUILD_DIR]:
        if folder.exists():
            shutil.rmtree(folder)
            print(f"  Supprimé: {folder}")

def collect_static():
    """Collecte les fichiers statiques Django."""
    print("\n[2/6] Collecte des fichiers statiques Django...")
    os.chdir(PROJECT_DIR)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestionnaire_rh.settings')
    
    result = run_command([
        sys.executable, 'manage.py', 'collectstatic', '--noinput'
    ], cwd=PROJECT_DIR)
    
    if not result:
        print("  ATTENTION: Erreur lors de la collecte des fichiers statiques")
    return True

def create_data_template():
    """Crée le template du dossier data."""
    print("\n[3/6] Création du template de données...")
    data_template = INSTALLER_DIR / 'data_template'
    data_template.mkdir(exist_ok=True)
    (data_template / 'logs').mkdir(exist_ok=True)
    (data_template / 'media').mkdir(exist_ok=True)
    
    # Créer un fichier README dans data
    readme = data_template / 'README.txt'
    readme.write_text("""GestionnaireRH - Dossier de données
====================================

Ce dossier contient:
- gestionnaire_rh.db : Base de données SQLite
- logs/ : Fichiers de journalisation
- media/ : Fichiers uploadés (photos, documents)

NE PAS SUPPRIMER ce dossier si vous souhaitez conserver vos données.
""", encoding='utf-8')
    print(f"  Créé: {data_template}")

def build_pyinstaller():
    """Construit l'exécutable avec PyInstaller."""
    print("\n[4/6] Construction de l'exécutable avec PyInstaller...")
    
    # Vérifier que PyInstaller est installé
    try:
        import PyInstaller
        print(f"  PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("  ERREUR: PyInstaller n'est pas installé!")
        print("  Installez-le avec: pip install pyinstaller")
        return False
    
    spec_file = INSTALLER_DIR / 'GestionnaireRH.spec'
    
    result = run_command([
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        '--distpath', str(DIST_DIR),
        '--workpath', str(BUILD_DIR),
        str(spec_file)
    ], cwd=PROJECT_DIR)
    
    if not result:
        print("  ERREUR: Échec de PyInstaller")
        return False
    
    # Vérifier que l'exe a été créé
    exe_path = DIST_DIR / 'GestionnaireRH' / 'GestionnaireRH.exe'
    if exe_path.exists():
        print(f"  SUCCESS: {exe_path}")
        return True
    else:
        print(f"  ERREUR: Exécutable non trouvé: {exe_path}")
        return False

def copy_additional_files():
    """Copie les fichiers additionnels dans le dossier dist."""
    print("\n[5/6] Copie des fichiers additionnels...")
    
    dist_app = DIST_DIR / 'GestionnaireRH'
    
    # Copier les templates si pas déjà inclus
    templates_src = PROJECT_DIR / 'templates'
    templates_dst = dist_app / 'templates'
    if templates_src.exists() and not templates_dst.exists():
        shutil.copytree(templates_src, templates_dst)
        print(f"  Copié: templates/")
    
    # Copier static si pas déjà inclus
    static_src = PROJECT_DIR / 'static'
    static_dst = dist_app / 'static'
    if static_src.exists() and not static_dst.exists():
        shutil.copytree(static_src, static_dst)
        print(f"  Copié: static/")
    
    # Copier staticfiles
    staticfiles_src = PROJECT_DIR / 'staticfiles'
    staticfiles_dst = dist_app / 'staticfiles'
    if staticfiles_src.exists() and not staticfiles_dst.exists():
        shutil.copytree(staticfiles_src, staticfiles_dst)
        print(f"  Copié: staticfiles/")
    
    # Créer le dossier data
    data_dir = dist_app / 'data'
    data_dir.mkdir(exist_ok=True)
    (data_dir / 'logs').mkdir(exist_ok=True)
    (data_dir / 'media').mkdir(exist_ok=True)
    print(f"  Créé: data/")

def build_inno_setup():
    """Construit l'installateur avec Inno Setup."""
    print("\n[6/6] Construction de l'installateur Inno Setup...")
    
    # Chercher Inno Setup
    inno_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
    ]
    
    iscc = None
    for path in inno_paths:
        if os.path.exists(path):
            iscc = path
            break
    
    if not iscc:
        print("  Inno Setup non trouvé.")
        print("  Pour créer l'installateur .exe, installez Inno Setup depuis:")
        print("  https://jrsoftware.org/isdl.php")
        print("\n  L'application portable est disponible dans:")
        print(f"  {DIST_DIR / 'GestionnaireRH'}")
        return False
    
    iss_file = INSTALLER_DIR / 'inno_setup.iss'
    output_dir = INSTALLER_DIR / 'output'
    output_dir.mkdir(exist_ok=True)
    
    result = run_command([iscc, str(iss_file)], cwd=INSTALLER_DIR)
    
    if result:
        print(f"\n  SUCCESS: Installateur créé dans {output_dir}")
        return True
    else:
        print("  ERREUR: Échec de Inno Setup")
        return False

def main():
    """Point d'entrée principal."""
    print("=" * 60)
    print("  GestionnaireRH - Construction de l'installateur Windows")
    print("=" * 60)
    
    # Étapes de construction
    clean_build()
    collect_static()
    create_data_template()
    
    if not build_pyinstaller():
        print("\n[ERREUR] La construction a échoué à l'étape PyInstaller")
        sys.exit(1)
    
    copy_additional_files()
    build_inno_setup()
    
    print("\n" + "=" * 60)
    print("  Construction terminée!")
    print("=" * 60)
    print(f"\nApplication portable: {DIST_DIR / 'GestionnaireRH'}")
    print(f"Lancez: {DIST_DIR / 'GestionnaireRH' / 'GestionnaireRH.exe'}")
    
    if (INSTALLER_DIR / 'output').exists():
        installers = list((INSTALLER_DIR / 'output').glob('*.exe'))
        if installers:
            print(f"\nInstallateur: {installers[0]}")

if __name__ == '__main__':
    main()
