#!/usr/bin/env python
"""
GestionnaireRH - Lanceur Windows
Lance le serveur Django et ouvre le navigateur automatiquement.
"""
import os
import sys
import time
import socket
import webbrowser
import threading
import subprocess
from pathlib import Path

# Déterminer le répertoire de l'application
if getattr(sys, 'frozen', False):
    # Mode exécutable (PyInstaller)
    APP_DIR = Path(sys.executable).parent
else:
    # Mode développement
    APP_DIR = Path(__file__).parent.parent

# Configuration
HOST = '127.0.0.1'
PORT = 8000
URL = f'http://{HOST}:{PORT}'

def find_free_port(start_port=8000):
    """Trouve un port libre à partir du port de départ."""
    port = start_port
    while port < start_port + 100:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((HOST, port))
                return port
        except OSError:
            port += 1
    return start_port

def wait_for_server(host, port, timeout=30):
    """Attend que le serveur soit prêt."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect((host, port))
                return True
        except (socket.error, socket.timeout):
            time.sleep(0.5)
    return False

def open_browser(url):
    """Ouvre le navigateur après un délai."""
    time.sleep(2)
    webbrowser.open(url)

def setup_environment():
    """Configure l'environnement pour Django."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestionnaire_rh.settings_portable_v2')
    
    # Définir les chemins
    data_dir = APP_DIR / 'data'
    data_dir.mkdir(exist_ok=True)
    
    os.environ['GESTIONNAIRE_RH_DATA_DIR'] = str(data_dir)
    os.environ['GESTIONNAIRE_RH_APP_DIR'] = str(APP_DIR)
    
    # Ajouter le répertoire de l'app au path
    if str(APP_DIR) not in sys.path:
        sys.path.insert(0, str(APP_DIR))

def run_migrations():
    """Exécute les migrations si nécessaire."""
    import django
    django.setup()
    
    from django.core.management import call_command
    from django.db import connection
    
    # Vérifier si la base de données existe et a des tables
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            if len(tables) < 5:  # Moins de 5 tables = DB vide ou incomplète
                print("Initialisation de la base de données...")
                call_command('migrate', '--run-syncdb', verbosity=0)
    except Exception as e:
        print(f"Migration: {e}")
        call_command('migrate', '--run-syncdb', verbosity=0)

def collect_static():
    """Collecte les fichiers statiques si nécessaire."""
    from django.core.management import call_command
    from django.conf import settings
    
    static_dir = Path(settings.STATIC_ROOT)
    if not static_dir.exists() or not any(static_dir.iterdir()):
        print("Collecte des fichiers statiques...")
        call_command('collectstatic', '--noinput', verbosity=0)

def create_superuser_if_needed():
    """Crée un superutilisateur par défaut si aucun n'existe."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if not User.objects.filter(is_superuser=True).exists():
        print("Création du compte administrateur par défaut...")
        User.objects.create_superuser(
            username='admin',
            email='admin@guineerh.local',
            password='admin123',
            first_name='Administrateur',
            last_name='Système'
        )
        print("Compte admin créé: admin / admin123")

def run_server(port):
    """Lance le serveur Django."""
    from django.core.management import call_command
    call_command('runserver', f'{HOST}:{port}', '--noreload')

def main():
    """Point d'entrée principal."""
    print("=" * 50)
    print("  GestionnaireRH - Système de Gestion RH Guinée")
    print("=" * 50)
    print()
    
    # Configuration de l'environnement
    print("Configuration de l'environnement...")
    setup_environment()
    
    # Trouver un port libre
    port = find_free_port(PORT)
    url = f'http://{HOST}:{port}'
    
    print(f"Port sélectionné: {port}")
    
    # Migrations et initialisation
    print("Vérification de la base de données...")
    run_migrations()
    
    print("Vérification des fichiers statiques...")
    collect_static()
    
    print("Vérification du compte administrateur...")
    create_superuser_if_needed()
    
    # Lancer le navigateur dans un thread séparé
    print(f"\nDémarrage du serveur sur {url}")
    print("Le navigateur va s'ouvrir automatiquement...")
    print("\nPour arrêter le serveur, fermez cette fenêtre ou appuyez sur Ctrl+C")
    print("-" * 50)
    
    browser_thread = threading.Thread(target=open_browser, args=(url,))
    browser_thread.daemon = True
    browser_thread.start()
    
    # Lancer le serveur (bloquant)
    try:
        run_server(port)
    except KeyboardInterrupt:
        print("\nArrêt du serveur...")
        sys.exit(0)

if __name__ == '__main__':
    main()
