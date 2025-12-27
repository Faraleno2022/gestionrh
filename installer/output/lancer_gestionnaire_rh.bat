@echo off
chcp 65001 >nul
title GestionnaireRH - Système de Gestion RH Guinée

echo ============================================================
echo   GestionnaireRH - Système de Gestion RH Guinée
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

echo [1/4] Vérification de l'environnement virtuel...
if not exist "venv\Scripts\activate.bat" (
    echo Création de l'environnement virtuel...
    python -m venv venv
)

echo [2/4] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

echo [3/4] Installation des dépendances...
pip install -q -r requirements.txt

echo [4/4] Démarrage du serveur...
echo.
echo ============================================================
echo   Le serveur démarre sur http://127.0.0.1:8000
echo   Le navigateur va s'ouvrir automatiquement.
echo.
echo   Pour arrêter: fermez cette fenêtre ou appuyez sur Ctrl+C
echo ============================================================
echo.

REM Ouvrir le navigateur après 3 secondes
start /b cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:8000"

REM Lancer le serveur Django
python manage.py runserver 127.0.0.1:8000

pause
