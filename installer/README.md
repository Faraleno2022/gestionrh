# GestionnaireRH - Guide de création de l'installateur Windows

## Prérequis

1. **Python 3.10+** avec pip
2. **PyInstaller** : `pip install pyinstaller`
3. **Inno Setup 6** (optionnel, pour créer l'installateur .exe) : 
   - Télécharger depuis https://jrsoftware.org/isdl.php

## Construction rapide

### Méthode 1 : Script automatique

```powershell
cd c:\Users\LENO\Desktop\GestionnaireRH
python installer\build_installer.py
```

### Méthode 2 : Étape par étape

```powershell
# 1. Installer PyInstaller
pip install pyinstaller

# 2. Collecter les fichiers statiques
python manage.py collectstatic --noinput

# 3. Construire l'exécutable
cd installer
pyinstaller --clean --noconfirm GestionnaireRH.spec

# 4. (Optionnel) Créer l'installateur avec Inno Setup
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" inno_setup.iss
```

## Résultats

Après la construction :

- **Application portable** : `installer/dist/GestionnaireRH/`
  - Peut être copiée sur une clé USB et exécutée directement
  - Lancez `GestionnaireRH.exe`

- **Installateur Windows** : `installer/output/GestionnaireRH_Setup_1.0.0.exe`
  - Installateur professionnel avec raccourcis bureau
  - Crée une entrée dans "Programmes et fonctionnalités"

## Structure de l'application installée

```
GestionnaireRH/
├── GestionnaireRH.exe      # Lanceur principal
├── data/                   # Données utilisateur (persistantes)
│   ├── gestionnaire_rh.db  # Base de données SQLite
│   ├── logs/               # Journaux
│   └── media/              # Fichiers uploadés
├── templates/              # Templates Django
├── static/                 # Fichiers statiques
└── staticfiles/            # Fichiers statiques collectés
```

## Utilisation

1. **Premier lancement** :
   - L'application crée automatiquement la base de données
   - Un compte admin par défaut est créé : `admin` / `admin123`
   - Le navigateur s'ouvre automatiquement sur http://127.0.0.1:8000

2. **Connexion** :
   - Utilisateur : `admin`
   - Mot de passe : `admin123`
   - **Changez ce mot de passe après la première connexion !**

3. **Arrêt** :
   - Fermez la fenêtre de console ou appuyez sur Ctrl+C

## Sauvegarde des données

Les données sont stockées dans le dossier `data/` :
- `gestionnaire_rh.db` : Toutes les données (employés, paie, etc.)
- `media/` : Photos et documents uploadés

Pour sauvegarder, copiez simplement le dossier `data/`.

## Dépannage

### Le serveur ne démarre pas
- Vérifiez qu'aucune autre application n'utilise le port 8000
- L'application essaiera automatiquement les ports 8001, 8002, etc.

### Erreur de base de données
- Supprimez `data/gestionnaire_rh.db` pour réinitialiser
- Attention : cela supprime toutes les données !

### Le navigateur ne s'ouvre pas
- Ouvrez manuellement http://127.0.0.1:8000 dans votre navigateur
