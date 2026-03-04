#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de déploiement pour ajouter les colonnes manquantes
À exécuter sur le serveur de production: python fix_deployment.py
"""

import os
import sys
import django
from django.conf import settings
from django.db import connection

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
django.setup()

def check_columns():
    """Vérifier si les colonnes existent"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'bulletins_paie' 
            AND COLUMN_NAME IN ('abattement_forfaitaire', 'base_vf', 'nombre_salaries')
        """)
        existing = {row[0] for row in cursor.fetchall()}
        return existing

def add_missing_columns():
    """Ajouter les colonnes manquantes via Django ORM"""
    from django.db import migrations
    from paie.models import BulletinPaie
    
    with connection.cursor() as cursor:
        # Ajouter abattement_forfaitaire
        try:
            cursor.execute("""
                ALTER TABLE bulletins_paie 
                ADD COLUMN abattement_forfaitaire DECIMAL(15, 2) DEFAULT 0.00
            """)
            print("✓ Colonne 'abattement_forfaitaire' ajoutée")
        except Exception as e:
            if "Duplicate column" in str(e):
                print("• Colonne 'abattement_forfaitaire' existe déjà")
            else:
                print(f"✗ Erreur abattement_forfaitaire: {e}")
                return False
        
        # Ajouter base_vf
        try:
            cursor.execute("""
                ALTER TABLE bulletins_paie 
                ADD COLUMN base_vf DECIMAL(15, 2) DEFAULT 0.00
            """)
            print("✓ Colonne 'base_vf' ajoutée")
        except Exception as e:
            if "Duplicate column" in str(e):
                print("• Colonne 'base_vf' existe déjà")
            else:
                print(f"✗ Erreur base_vf: {e}")
                return False
        
        # Ajouter nombre_salaries
        try:
            cursor.execute("""
                ALTER TABLE bulletins_paie 
                ADD COLUMN nombre_salaries INT DEFAULT 0
            """)
            print("✓ Colonne 'nombre_salaries' ajoutée")
        except Exception as e:
            if "Duplicate column" in str(e):
                print("• Colonne 'nombre_salaries' existe déjà")
            else:
                print(f"✗ Erreur nombre_salaries: {e}")
                return False
        
        # Ajouter les index
        try:
            cursor.execute("""
                CREATE INDEX idx_abattement_forfaitaire 
                ON bulletins_paie(abattement_forfaitaire)
            """)
            print("✓ Index sur 'abattement_forfaitaire' créé")
        except:
            print("• Index sur 'abattement_forfaitaire' existe déjà")
        
        try:
            cursor.execute("""
                CREATE INDEX idx_base_vf 
                ON bulletins_paie(base_vf)
            """)
            print("✓ Index sur 'base_vf' créé")
        except:
            print("• Index sur 'base_vf' existe déjà")
        
        try:
            cursor.execute("""
                CREATE INDEX idx_nombre_salaries 
                ON bulletins_paie(nombre_salaries)
            """)
            print("✓ Index sur 'nombre_salaries' créé")
        except:
            print("• Index sur 'nombre_salaries' existe déjà")
    
    return True

def apply_migration():
    """Appliquer la migration Django"""
    from django.core.management import call_command
    
    try:
        print("\n📦 Application de la migration Django...")
        call_command('migrate', 'paie', verbosity=2)
        print("✓ Migration appliquée avec succès")
        return True
    except Exception as e:
        print(f"✗ Erreur lors de la migration: {e}")
        return False

def main():
    print("=" * 60)
    print("🔧 Correctif de déploiement - Colonnes manquantes")
    print("=" * 60)
    
    # 1. Vérifier les colonnes actuelles
    print("\n📋 Vérification des colonnes existantes...")
    existing = check_columns()
    missing = {'abattement_forfaitaire', 'base_vf', 'nombre_salaries'} - existing
    
    if not missing:
        print("✓ Toutes les colonnes existent déjà!")
        print(f"  Colonnes présentes: {existing}")
        return True
    
    print(f"✗ Colonnes manquantes: {missing}")
    
    # 2. Ajouter les colonnes manuellement
    print("\n🔨 Ajout des colonnes manquantes...")
    if not add_missing_columns():
        print("✗ Impossible d'ajouter les colonnes")
        return False
    
    # 3. Appliquer la migration Django
    print("\n✅ Colonnes ajoutées avec succès!")
    print("\n📦 Application de la migration complète...")
    apply_migration()
    
    # 4. Vérification finale
    print("\n✓ Vérification finale...")
    final = check_columns()
    if final == {'abattement_forfaitaire', 'base_vf', 'nombre_salaries'}:
        print("✓✓✓ SUCCÈS ! Toutes les colonnes sont présentes")
        print(f"    Colonnes confirmées: {final}")
        print("\n🎉 Le système est prêt à fonctionner!")
        print("\n📌 Prochaines étapes:")
        print("   1. Redémarrer uWSGI/WSGI")
        print("   2. Accéder à /paie/periodes/ pour vérifier")
        return True
    else:
        print("✗ Erreur: certaines colonnes manquent toujours")
        print(f"   Présentes: {final}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
