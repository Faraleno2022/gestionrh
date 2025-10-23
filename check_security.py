#!/usr/bin/env python
"""
Script de vérification de la configuration de sécurité
"""
import os
import sys
from pathlib import Path

# Couleurs pour le terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}\n")


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


def check_env_file():
    """Vérifie l'existence et la configuration du fichier .env"""
    print_header("Vérification du fichier .env")
    
    if not os.path.exists('.env'):
        print_error("Fichier .env non trouvé")
        print_info("Créez-le avec: cp .env.example .env")
        return False
    
    print_success("Fichier .env trouvé")
    
    # Vérifier les variables critiques
    critical_vars = [
        'SECRET_KEY',
        'DEBUG',
        'ALLOWED_HOSTS',
    ]
    
    with open('.env', 'r') as f:
        env_content = f.read()
    
    missing_vars = []
    for var in critical_vars:
        if var not in env_content:
            missing_vars.append(var)
    
    if missing_vars:
        print_warning(f"Variables manquantes: {', '.join(missing_vars)}")
        return False
    
    # Vérifier si SECRET_KEY est par défaut
    if 'your-secret-key-here' in env_content:
        print_error("SECRET_KEY utilise la valeur par défaut - CHANGEZ-LA!")
        return False
    
    print_success("Variables critiques présentes")
    return True


def check_security_packages():
    """Vérifie l'installation des packages de sécurité"""
    print_header("Vérification des packages de sécurité")
    
    required_packages = [
        'django',
        'django-axes',
        'django-defender',
        'django-csp',
        'cryptography',
        'bleach',
        'django-ratelimit',
    ]
    
    all_installed = True
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print_success(f"{package} installé")
        except ImportError:
            print_error(f"{package} NON installé")
            all_installed = False
    
    if not all_installed:
        print_info("Installez les packages manquants avec: pip install -r requirements.txt")
    
    return all_installed


def check_logs_directory():
    """Vérifie l'existence du répertoire logs"""
    print_header("Vérification du répertoire logs")
    
    logs_dir = Path('logs')
    
    if not logs_dir.exists():
        print_warning("Répertoire logs non trouvé")
        print_info("Créez-le avec: mkdir logs")
        return False
    
    print_success("Répertoire logs trouvé")
    
    # Vérifier les permissions
    if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
        print_success("Permissions d'écriture OK")
        return True
    else:
        print_error("Pas de permission d'écriture sur le répertoire logs")
        return False


def check_gitignore():
    """Vérifie que .gitignore protège les fichiers sensibles"""
    print_header("Vérification du .gitignore")
    
    if not os.path.exists('.gitignore'):
        print_error("Fichier .gitignore non trouvé")
        return False
    
    print_success("Fichier .gitignore trouvé")
    
    with open('.gitignore', 'r') as f:
        gitignore_content = f.read()
    
    critical_patterns = ['.env', '*.log', 'db.sqlite3', '*.key', '*.pem']
    
    missing_patterns = []
    for pattern in critical_patterns:
        if pattern not in gitignore_content:
            missing_patterns.append(pattern)
    
    if missing_patterns:
        print_warning(f"Patterns manquants dans .gitignore: {', '.join(missing_patterns)}")
        return False
    
    print_success("Fichiers sensibles protégés")
    return True


def check_middleware():
    """Vérifie la configuration des middlewares de sécurité"""
    print_header("Vérification des middlewares")
    
    try:
        # Importer settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestionnaire_rh.settings')
        import django
        django.setup()
        from django.conf import settings
        
        required_middleware = [
            'django.middleware.security.SecurityMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
            'axes.middleware.AxesMiddleware',
        ]
        
        all_present = True
        for middleware in required_middleware:
            if middleware in settings.MIDDLEWARE:
                print_success(f"{middleware.split('.')[-1]} activé")
            else:
                print_error(f"{middleware.split('.')[-1]} NON activé")
                all_present = False
        
        return all_present
        
    except Exception as e:
        print_error(f"Erreur lors de la vérification: {e}")
        return False


def check_security_settings():
    """Vérifie les paramètres de sécurité Django"""
    print_header("Vérification des paramètres de sécurité")
    
    try:
        from django.conf import settings
        
        checks = [
            ('DEBUG', False, "DEBUG devrait être False en production"),
            ('SECURE_BROWSER_XSS_FILTER', True, "XSS Filter devrait être activé"),
            ('SECURE_CONTENT_TYPE_NOSNIFF', True, "Content Type Nosniff devrait être activé"),
            ('X_FRAME_OPTIONS', 'DENY', "X-Frame-Options devrait être DENY"),
            ('SESSION_COOKIE_HTTPONLY', True, "Session Cookie HttpOnly devrait être activé"),
            ('CSRF_COOKIE_HTTPONLY', True, "CSRF Cookie HttpOnly devrait être activé"),
        ]
        
        all_ok = True
        for setting_name, expected_value, message in checks:
            actual_value = getattr(settings, setting_name, None)
            
            if actual_value == expected_value:
                print_success(f"{setting_name} = {actual_value}")
            else:
                if setting_name == 'DEBUG' and actual_value == True:
                    print_warning(f"{setting_name} = {actual_value} (OK pour développement)")
                else:
                    print_warning(f"{setting_name} = {actual_value} (attendu: {expected_value})")
                    print_info(f"  → {message}")
                    all_ok = False
        
        return all_ok
        
    except Exception as e:
        print_error(f"Erreur lors de la vérification: {e}")
        return False


def check_database():
    """Vérifie la configuration de la base de données"""
    print_header("Vérification de la base de données")
    
    try:
        from django.conf import settings
        
        db_engine = settings.DATABASES['default']['ENGINE']
        
        if 'sqlite3' in db_engine:
            print_warning("SQLite détecté - PostgreSQL recommandé pour la production")
        elif 'postgresql' in db_engine:
            print_success("PostgreSQL configuré")
        else:
            print_info(f"Base de données: {db_engine}")
        
        # Vérifier si le fichier de base de données existe (pour SQLite)
        if 'sqlite3' in db_engine:
            db_path = settings.DATABASES['default']['NAME']
            if os.path.exists(db_path):
                print_success("Fichier de base de données trouvé")
            else:
                print_warning("Fichier de base de données non trouvé - Exécutez: python manage.py migrate")
        
        return True
        
    except Exception as e:
        print_error(f"Erreur lors de la vérification: {e}")
        return False


def generate_report():
    """Génère un rapport complet"""
    print_header("RAPPORT DE SÉCURITÉ - Gestionnaire RH Guinée")
    
    results = {
        'Fichier .env': check_env_file(),
        'Packages de sécurité': check_security_packages(),
        'Répertoire logs': check_logs_directory(),
        'Fichier .gitignore': check_gitignore(),
        'Middlewares': check_middleware(),
        'Paramètres de sécurité': check_security_settings(),
        'Base de données': check_database(),
    }
    
    print_header("RÉSUMÉ")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for check, result in results.items():
        if result:
            print_success(f"{check}: OK")
        else:
            print_error(f"{check}: ÉCHEC")
    
    print(f"\n{Colors.BOLD}Score de sécurité: {passed}/{total} ({int(passed/total*100)}%){Colors.END}\n")
    
    if passed == total:
        print_success("Toutes les vérifications sont passées! ✓")
    elif passed >= total * 0.7:
        print_warning("Certaines vérifications ont échoué. Consultez les détails ci-dessus.")
    else:
        print_error("Plusieurs vérifications ont échoué. Action requise!")
    
    print(f"\n{Colors.BLUE}Pour plus d'informations, consultez:{Colors.END}")
    print(f"  - README_SECURITE.md")
    print(f"  - SECURITY.md")
    print(f"  - INSTALLATION_SECURITE.md\n")


if __name__ == '__main__':
    try:
        generate_report()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Vérification interrompue{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Erreur: {e}{Colors.END}")
        sys.exit(1)
