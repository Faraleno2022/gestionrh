#!/usr/bin/env python
"""
Script pour corriger automatiquement les problèmes CSP dans settings.py
Compatible avec django-csp 4.0+
"""

import re
import os
import sys
from pathlib import Path

# Chemin du fichier settings
BASE_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = BASE_DIR / "gestionnaire_rh" / "settings.py"

# Nouvelle configuration CSP assouplie pour la production
NEW_CSP_CONFIG = """# Content Security Policy (django-csp 4.0+ format)
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ("'self'",),
        'script-src': ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://code.jquery.com", "https://stackpath.bootstrapcdn.com"),
        'style-src': ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://fonts.googleapis.com", "https://stackpath.bootstrapcdn.com"),
        'font-src': ("'self'", "https://fonts.gstatic.com", "https://cdn.jsdelivr.net"),
        'img-src': ("'self'", "data:", "https:", "blob:"),
        'connect-src': ("'self'",),
        'frame-ancestors': ("'none'",),
        'base-uri': ("'self'",),
        'form-action': ("'self'",),
        'media-src': ("'self'", "data:", "https:"),
        'object-src': ("'none'",),
        'worker-src': ("'self'", "blob:"),
    }
}"""


def backup_file(filepath):
    """Créer une sauvegarde du fichier"""
    backup_path = f"{filepath}.backup"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Sauvegarde créée: {backup_path}")
    return backup_path


def fix_csp_settings(filepath):
    """Corriger les paramètres CSP dans settings.py"""
    
    if not os.path.exists(filepath):
        print(f"❌ Erreur: Le fichier {filepath} n'existe pas!")
        return False
    
    # Créer une sauvegarde
    backup_file(filepath)
    
    # Lire le contenu du fichier
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern pour trouver la configuration CSP existante
    csp_pattern = r"# Content Security Policy.*?CONTENT_SECURITY_POLICY\s*=\s*\{[^}]*\{[^}]*\}[^}]*\}"
    
    # Vérifier si la configuration CSP existe
    if re.search(csp_pattern, content, re.DOTALL):
        # Remplacer la configuration existante
        new_content = re.sub(csp_pattern, NEW_CSP_CONFIG, content, flags=re.DOTALL)
        print("✅ Configuration CSP existante trouvée et mise à jour")
    else:
        # Chercher où insérer la nouvelle configuration
        # Après les paramètres de sécurité
        security_pattern = r"(# Clickjacking Protection\s*\nX_FRAME_OPTIONS\s*=\s*['\"]DENY['\"])"
        
        if re.search(security_pattern, content):
            new_content = re.sub(
                security_pattern,
                r"\1\n\n" + NEW_CSP_CONFIG,
                content
            )
            print("✅ Configuration CSP ajoutée après X_FRAME_OPTIONS")
        else:
            print("⚠️  Impossible de trouver l'emplacement pour insérer CSP")
            print("    Ajoutez manuellement la configuration CSP dans settings.py")
            return False
    
    # Écrire le nouveau contenu
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Fichier {filepath} mis à jour avec succès!")
    return True


def verify_csp_settings(filepath):
    """Vérifier que les paramètres CSP sont corrects"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_directives = [
        "'unsafe-inline'",
        "https://cdn.jsdelivr.net",
        "https://code.jquery.com",
        "https://fonts.googleapis.com",
        "https://fonts.gstatic.com"
    ]
    
    all_present = all(directive in content for directive in required_directives)
    
    if all_present:
        print("✅ Tous les directives CSP requis sont présents")
        return True
    else:
        print("⚠️  Certains directives CSP sont manquants")
        return False


def main():
    """Fonction principale"""
    print("=" * 60)
    print("🔧 Script de Correction CSP pour Django")
    print("=" * 60)
    print()
    
    if not SETTINGS_FILE.exists():
        print(f"❌ Erreur: {SETTINGS_FILE} n'existe pas!")
        print(f"   Chemin recherché: {SETTINGS_FILE.absolute()}")
        sys.exit(1)
    
    print(f"📁 Fichier à modifier: {SETTINGS_FILE}")
    print()
    
    # Demander confirmation
    response = input("Voulez-vous continuer? (o/n): ").lower()
    if response != 'o':
        print("❌ Opération annulée")
        sys.exit(0)
    
    print()
    print("🔄 Correction en cours...")
    print()
    
    # Corriger les paramètres CSP
    if fix_csp_settings(SETTINGS_FILE):
        print()
        print("🔍 Vérification de la configuration...")
        verify_csp_settings(SETTINGS_FILE)
        print()
        print("=" * 60)
        print("✅ CORRECTION TERMINÉE AVEC SUCCÈS!")
        print("=" * 60)
        print()
        print("📝 Prochaines étapes:")
        print("   1. Vérifiez le fichier settings.py")
        print("   2. Sur PythonAnywhere, cliquez sur 'Reload'")
        print("   3. Testez votre site: https://www.guineerh.space")
        print()
        print("💾 Une sauvegarde a été créée: settings.py.backup")
        print()
    else:
        print()
        print("=" * 60)
        print("❌ ERREUR LORS DE LA CORRECTION")
        print("=" * 60)
        print()
        print("Veuillez corriger manuellement en ajoutant:")
        print(NEW_CSP_CONFIG)
        sys.exit(1)


if __name__ == "__main__":
    main()
