@echo off
chcp 65001 >nul
title GestionnaireRH - Premier Démarrage

echo ============================================================
echo   GestionnaireRH - Installation et Premier Démarrage
echo ============================================================
echo.

cd /d "%~dp0"

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installé ou n'est pas dans le PATH.
    echo.
    echo Veuillez installer Python depuis https://www.python.org/downloads/
    echo Cochez "Add Python to PATH" lors de l'installation.
    echo.
    pause
    exit /b 1
)

echo [1/6] Création de l'environnement virtuel...
if not exist "venv\Scripts\activate.bat" (
    python -m venv venv
)

echo [2/6] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

echo [3/6] Installation des dépendances (cela peut prendre quelques minutes)...
pip install -q -r requirements.txt

echo [4/6] Initialisation de la base de données...
python manage.py migrate --run-syncdb

echo [5/6] Collecte des fichiers statiques...
python manage.py collectstatic --noinput

echo [6/6] Création du compte administrateur...
echo.
echo Un compte administrateur par défaut va être créé:
echo   Utilisateur: admin
echo   Mot de passe: admin123
echo.
python -c "import django; django.setup(); from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@guineerh.local', 'admin123', first_name='Admin', last_name='Système')" 2>nul

echo.
echo ============================================================
echo   Installation terminée!
echo ============================================================
echo.
echo   Compte administrateur:
echo     Utilisateur: admin
echo     Mot de passe: admin123
echo.
echo   IMPORTANT: Changez ce mot de passe après la première connexion!
echo.
echo   Pour lancer l'application, utilisez: lancer_gestionnaire_rh.bat
echo.
pause
