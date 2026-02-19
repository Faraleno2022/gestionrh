@echo off
title Build GestionnaireRH - Executable Complet

echo ============================================
echo   BUILD GESTIONNAIRE RH v1.1.0
echo   Executable avec raccourci bureau + desinstallateur
echo ============================================
echo.

python --version
if errorlevel 1 (
    echo [ERREUR] Python non trouve! Installez Python 3.10+
    pause
    exit /b 1
)
echo.

echo [1/5] Collecte des fichiers statiques...
python manage.py collectstatic --noinput
echo.

echo [2/5] Nettoyage des builds precedents...
if exist dist\GestionnaireRH rmdir /s /q dist\GestionnaireRH
if exist build rmdir /s /q build
echo   Nettoyage OK
echo.

echo [3/5] Preparation du dossier data_template...
if not exist data_template mkdir data_template
if not exist data_template\logs mkdir data_template\logs
if not exist data_template\media mkdir data_template\media
echo   data_template OK
echo.

echo [4/5] Build PyInstaller (cela peut prendre 5-10 minutes)...
echo.

pyinstaller --clean --noconfirm --distpath dist --workpath build GestionnaireRH_build.spec

if errorlevel 1 (
    echo.
    echo [ERREUR] Build PyInstaller echoue!
    echo Verifiez que PyInstaller est installe: pip install pyinstaller
    pause
    exit /b 1
)

echo.
echo   Copie des fichiers supplementaires...
if not exist dist\GestionnaireRH\data mkdir dist\GestionnaireRH\data
if not exist dist\GestionnaireRH\data\logs mkdir dist\GestionnaireRH\data\logs
if not exist dist\GestionnaireRH\data\media mkdir dist\GestionnaireRH\data\media

if not exist dist\GestionnaireRH\templates xcopy /E /I /Y templates dist\GestionnaireRH\templates >nul 2>nul
if not exist dist\GestionnaireRH\static xcopy /E /I /Y static dist\GestionnaireRH\static >nul 2>nul
if not exist dist\GestionnaireRH\staticfiles xcopy /E /I /Y staticfiles dist\GestionnaireRH\staticfiles >nul 2>nul

echo   Build PyInstaller OK
echo.

echo [5/5] Copie des scripts d'installation et desinstallation...
echo.

copy /Y scripts\Installer.bat dist\GestionnaireRH\Installer.bat >nul
copy /Y scripts\Desinstaller.bat dist\GestionnaireRH\Desinstaller.bat >nul

echo   Scripts copies dans dist\GestionnaireRH\
echo.

:end
echo.
echo ============================================
echo   BUILD TERMINE AVEC SUCCES!
echo ============================================
echo.
echo Resultats:
echo.
if exist dist\GestionnaireRH\GestionnaireRH.exe echo   [OK] Executable: dist\GestionnaireRH\GestionnaireRH.exe
if exist dist\GestionnaireRH\Installer.bat echo   [OK] Installateur: dist\GestionnaireRH\Installer.bat
if exist dist\GestionnaireRH\Demarrer.bat echo   [OK] Lanceur: dist\GestionnaireRH\Demarrer.bat
echo.
echo Pour distribuer:
echo 1. Copiez le dossier "dist\GestionnaireRH" sur une clé USB
echo 2. Sur le PC client, executez "Installer.bat"
echo 3. L'application sera installee dans C:\GestionnaireRH avec:
echo    - Raccourci sur le Bureau
echo    - Raccourci dans le menu Demarrer
echo    - Desinstallateur dans le menu Demarrer
echo.
pause
