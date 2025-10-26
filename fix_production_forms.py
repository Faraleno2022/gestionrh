#!/usr/bin/env python
"""
Script de diagnostic et correction des problèmes de formulaires en production
"""

import os
import sys
from pathlib import Path

# Couleurs pour le terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def check_static_files():
    """Vérifier la configuration des fichiers statiques"""
    print("\n" + "="*60)
    print("🔍 VÉRIFICATION DES FICHIERS STATIQUES")
    print("="*60 + "\n")
    
    base_dir = Path(__file__).resolve().parent
    
    # Vérifier les dossiers
    static_dir = base_dir / 'static'
    staticfiles_dir = base_dir / 'staticfiles'
    
    if static_dir.exists():
        print_success(f"Dossier 'static' existe: {static_dir}")
    else:
        print_warning(f"Dossier 'static' n'existe pas: {static_dir}")
        print_info("Création du dossier...")
        static_dir.mkdir(exist_ok=True)
        print_success("Dossier 'static' créé")
    
    if staticfiles_dir.exists():
        print_success(f"Dossier 'staticfiles' existe: {staticfiles_dir}")
    else:
        print_warning(f"Dossier 'staticfiles' n'existe pas")
        print_info("Sera créé lors de 'collectstatic'")
    
    return True

def check_templates():
    """Vérifier les templates de formulaires"""
    print("\n" + "="*60)
    print("🔍 VÉRIFICATION DES TEMPLATES")
    print("="*60 + "\n")
    
    base_dir = Path(__file__).resolve().parent
    templates_dir = base_dir / 'templates'
    
    if not templates_dir.exists():
        print_error("Dossier 'templates' n'existe pas!")
        return False
    
    print_success(f"Dossier 'templates' existe: {templates_dir}")
    
    # Vérifier base.html
    base_template = templates_dir / 'base.html'
    if base_template.exists():
        print_success("Template 'base.html' trouvé")
        
        # Vérifier le chargement des fichiers statiques
        with open(base_template, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if '{% load static %}' in content:
            print_success("'{% load static %}' présent dans base.html")
        else:
            print_warning("'{% load static %}' manquant dans base.html")
        
        if 'bootstrap' in content.lower():
            print_success("Bootstrap détecté dans base.html")
        else:
            print_warning("Bootstrap non détecté dans base.html")
    else:
        print_error("Template 'base.html' non trouvé!")
        return False
    
    return True

def create_diagnostic_commands():
    """Créer un fichier avec les commandes de diagnostic"""
    print("\n" + "="*60)
    print("📝 CRÉATION DES COMMANDES DE DIAGNOSTIC")
    print("="*60 + "\n")
    
    commands = """#!/bin/bash
# Commandes de diagnostic pour la production

echo "=========================================="
echo "🔍 DIAGNOSTIC DE PRODUCTION"
echo "=========================================="
echo ""

# 1. Vérifier l'environnement virtuel
echo "1️⃣  Vérification de l'environnement virtuel..."
which python
python --version
echo ""

# 2. Vérifier les variables d'environnement
echo "2️⃣  Vérification des variables d'environnement..."
echo "DEBUG: $DEBUG"
echo "DB_ENGINE: $DB_ENGINE"
echo "ALLOWED_HOSTS: $ALLOWED_HOSTS"
echo ""

# 3. Vérifier les dossiers statiques
echo "3️⃣  Vérification des dossiers statiques..."
ls -la static/ 2>/dev/null || echo "❌ Dossier 'static' n'existe pas"
ls -la staticfiles/ 2>/dev/null || echo "❌ Dossier 'staticfiles' n'existe pas"
echo ""

# 4. Vérifier les dépendances
echo "4️⃣  Vérification des dépendances critiques..."
pip show django crispy-bootstrap5 django-widget-tweaks
echo ""

# 5. Tester la configuration Django
echo "5️⃣  Test de la configuration Django..."
python manage.py check
echo ""

# 6. Collecter les fichiers statiques
echo "6️⃣  Collection des fichiers statiques..."
python manage.py collectstatic --noinput
echo ""

# 7. Vérifier les migrations
echo "7️⃣  Vérification des migrations..."
python manage.py showmigrations
echo ""

echo "=========================================="
echo "✅ DIAGNOSTIC TERMINÉ"
echo "=========================================="
"""
    
    diagnostic_file = Path(__file__).resolve().parent / 'diagnostic_production.sh'
    with open(diagnostic_file, 'w', encoding='utf-8') as f:
        f.write(commands)
    
    # Rendre le fichier exécutable
    os.chmod(diagnostic_file, 0o755)
    
    print_success(f"Fichier de diagnostic créé: {diagnostic_file}")
    print_info("Exécutez: bash diagnostic_production.sh")
    
    return True

def create_fix_script():
    """Créer un script de correction automatique"""
    print("\n" + "="*60)
    print("🔧 CRÉATION DU SCRIPT DE CORRECTION")
    print("="*60 + "\n")
    
    fix_script = """#!/bin/bash
# Script de correction automatique pour la production

echo "=========================================="
echo "🔧 CORRECTION AUTOMATIQUE"
echo "=========================================="
echo ""

# Activer l'environnement virtuel
source venv/bin/activate

# Charger les variables d'environnement
export $(cat .env | xargs)

# 1. Installer/Mettre à jour les dépendances
echo "1️⃣  Installation des dépendances..."
pip install --upgrade pip
pip install -r requirements.txt
echo ""

# 2. Créer les dossiers nécessaires
echo "2️⃣  Création des dossiers..."
mkdir -p static
mkdir -p staticfiles
mkdir -p media
mkdir -p media/entreprises/logos
echo "✅ Dossiers créés"
echo ""

# 3. Collecter les fichiers statiques
echo "3️⃣  Collection des fichiers statiques..."
python manage.py collectstatic --clear --noinput
echo ""

# 4. Appliquer les migrations
echo "4️⃣  Application des migrations..."
python manage.py migrate
echo ""

# 5. Vérifier la configuration
echo "5️⃣  Vérification de la configuration..."
python manage.py check --deploy
echo ""

echo "=========================================="
echo "✅ CORRECTION TERMINÉE"
echo "=========================================="
echo ""
echo "📝 Prochaines étapes:"
echo "   1. Sur PythonAnywhere, cliquez 'Reload'"
echo "   2. Testez votre site"
echo "   3. Vérifiez la console du navigateur (F12)"
echo ""
"""
    
    fix_file = Path(__file__).resolve().parent / 'fix_production.sh'
    with open(fix_file, 'w', encoding='utf-8') as f:
        f.write(fix_script)
    
    # Rendre le fichier exécutable
    os.chmod(fix_file, 0o755)
    
    print_success(f"Script de correction créé: {fix_file}")
    print_info("Exécutez: bash fix_production.sh")
    
    return True

def main():
    """Fonction principale"""
    print("\n" + "="*60)
    print("🔍 DIAGNOSTIC DES FORMULAIRES EN PRODUCTION")
    print("="*60)
    
    # Vérifications
    check_static_files()
    check_templates()
    create_diagnostic_commands()
    create_fix_script()
    
    print("\n" + "="*60)
    print("📋 RÉSUMÉ DES PROBLÈMES COURANTS")
    print("="*60 + "\n")
    
    print("🔴 Problème 1: Fichiers statiques non chargés")
    print("   Solution: python manage.py collectstatic --noinput")
    print("")
    
    print("🔴 Problème 2: Bootstrap/CSS manquants")
    print("   Solution: Vérifier STATICFILES_DIRS dans settings.py")
    print("")
    
    print("🔴 Problème 3: Formulaires crispy non stylés")
    print("   Solution: pip install crispy-bootstrap5")
    print("")
    
    print("🔴 Problème 4: Erreurs CSP bloquant les styles")
    print("   Solution: python fix_csp.py")
    print("")
    
    print("🔴 Problème 5: DEBUG=True en production")
    print("   Solution: Vérifier .env (DEBUG=False)")
    print("")
    
    print("="*60)
    print("✅ SCRIPTS CRÉÉS")
    print("="*60 + "\n")
    
    print("1️⃣  diagnostic_production.sh - Diagnostic complet")
    print("2️⃣  fix_production.sh - Correction automatique")
    print("")
    
    print("🚀 COMMANDES RAPIDES:")
    print("")
    print("   # Sur le serveur de production:")
    print("   cd ~/ETRAGC_SARLU/gestionrh")
    print("   bash fix_production.sh")
    print("")
    print("   # Puis sur PythonAnywhere:")
    print("   Onglet Web > Bouton 'Reload' 🔄")
    print("")

if __name__ == "__main__":
    main()
