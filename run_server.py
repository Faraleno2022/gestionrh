#!/usr/bin/env python
"""
Script de lancement du serveur Django pour PyInstaller
Gestionnaire RH Guinée - Version Offline
"""
import os
import sys
import webbrowser
import threading
import time

def open_browser():
    """Ouvre le navigateur après un délai"""
    time.sleep(3)
    webbrowser.open('http://127.0.0.1:8000/')

def main():
    # Définir le chemin de base
    if getattr(sys, 'frozen', False):
        # Exécuté depuis l'exécutable PyInstaller
        base_dir = os.path.dirname(sys.executable)
        # PyInstaller extrait les fichiers dans _MEIPASS
        internal_dir = sys._MEIPASS
    else:
        # Exécuté depuis Python
        base_dir = os.path.dirname(os.path.abspath(__file__))
        internal_dir = base_dir
    
    # Changer vers le répertoire de l'exécutable (pour db.sqlite3, media, etc.)
    os.chdir(base_dir)
    
    # Ajouter les chemins au path
    if internal_dir not in sys.path:
        sys.path.insert(0, internal_dir)
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)
    
    # Configurer Django AVANT tout import Django
    os.environ['DJANGO_SETTINGS_MODULE'] = 'gestionnaire_rh.settings'
    
    # Forcer le chemin des templates et static pour PyInstaller
    if getattr(sys, 'frozen', False):
        os.environ['PYINSTALLER_BASE_DIR'] = base_dir
        os.environ['PYINSTALLER_INTERNAL_DIR'] = internal_dir
    
    try:
        # Importer Django après configuration
        import django
        django.setup()
        
        from django.core.management import execute_from_command_line
        
        print("=" * 50)
        print("  GESTIONNAIRE RH GUINEE - VERSION OFFLINE")
        print("=" * 50)
        print()
        
        # Vérifier si la base de données existe, sinon la créer
        db_path = os.path.join(base_dir, 'db.sqlite3')
        if os.path.exists(db_path):
            print("  Base de donnees OK")
        else:
            print("  Base de donnees absente - creation en cours...")
        
        # Toujours appliquer les migrations (crée la DB si absente)
        try:
            execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
            print("  Migrations appliquees avec succes")
        except Exception as e:
            print(f"  Erreur migration: {e}")
        
        print()
        print("  Serveur demarre sur: http://127.0.0.1:8000/")
        print()
        print("  Appuyez sur CTRL+C pour arreter")
        print("=" * 50)
        print()
        
        # Ouvrir le navigateur dans un thread séparé
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Lancer le serveur sans rechargement automatique
        execute_from_command_line(['manage.py', 'runserver', '--noreload', '127.0.0.1:8000'])
        
    except KeyboardInterrupt:
        print("\nServeur arrete.")
        sys.exit(0)
    except Exception as e:
        import traceback
        print(f"Erreur: {e}")
        print()
        traceback.print_exc()
        print()
        input("Appuyez sur Entree pour fermer...")
        sys.exit(1)

if __name__ == '__main__':
    main()
