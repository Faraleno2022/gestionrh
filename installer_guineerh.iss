; GestionnaireRH - Inno Setup Installer Script
; ===============================================
; Auteur  : Guinée RH
; Version : 1.0.0
;
; Prérequis : Inno Setup 6+ (https://jrsoftware.org/isinfo.php)
;
; Pour compiler :
;   1. Installez Inno Setup
;   2. Ouvrez ce fichier dans Inno Setup Compiler
;   3. Appuyez sur Ctrl+F9 (Compile)
;   4. L'installateur est créé dans le dossier "Output"

[Setup]
; ── Identification ─────────────────────────────────────────────────────────────
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName=GestionnaireRH
AppVersion=1.0.0
AppVerName=GestionnaireRH 1.0.0
AppPublisher=Guinée RH
AppPublisherURL=https://www.guineerh.space
AppSupportURL=https://www.guineerh.space
AppCopyright=Copyright © 2024 Guinée RH. Tous droits réservés.

; ── Installation ───────────────────────────────────────────────────────────────
DefaultDirName={autopf}\GestionnaireRH
DefaultGroupName=GestionnaireRH
AllowNoIcons=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; ── Sortie ─────────────────────────────────────────────────────────────────────
OutputDir=Output
OutputBaseFilename=GestionnaireRH_Setup_v1.0.0

; ── Icône ───────────────────────────────────────────────────────────────────────
SetupIconFile=static\img\logo.ico

; ── Compression ────────────────────────────────────────────────────────────────
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

; ── Interface ──────────────────────────────────────────────────────────────────
WizardStyle=modern
WizardSizePercent=100
WizardResizable=no
DisableWelcomePage=no

; ── Désinstallation ────────────────────────────────────────────────────────────
UninstallDisplayName=GestionnaireRH - Système de Gestion RH
UninstallDisplayIcon={app}\GestionnaireRH.exe
CreateUninstallRegKey=yes

; ── Version info (visible dans Programmes et fonctionnalités) ──────────────────
VersionInfoVersion=1.0.0.0
VersionInfoCompany=Guinée RH
VersionInfoDescription=GestionnaireRH - Système de Gestion des Ressources Humaines
VersionInfoCopyright=Copyright © 2024 Guinée RH

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon";   Description: "Créer un raccourci sur le Bureau";         GroupDescription: "Raccourcis :"
Name: "startmenuicon"; Description: "Créer une entrée dans le menu Démarrer";   GroupDescription: "Raccourcis :"
Name: "autostart";     Description: "Lancer GestionnaireRH au démarrage de Windows"; GroupDescription: "Options :"; Flags: unchecked

[Files]
; Application compilée (tout le dossier dist\GestionnaireRH)
Source: "dist\GestionnaireRH\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Script de désinstallation
Source: "desinstaller.bat"; DestDir: "{app}"; Flags: ignoreversion

; Script d'arrêt du serveur (raccourci menu Démarrer)
Source: "Arreter_GestionnaireRH.bat"; DestDir: "{app}"; Flags: ignoreversion

; Outil d'activation de licence (pour le technicien)
Source: "license_manager.py"; DestDir: "{app}"; Flags: ignoreversion

; Icône
Source: "static\img\logo.ico"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Dossiers avec permissions d'écriture
Name: "{app}\logs";               Permissions: users-modify
Name: "{app}\media";              Permissions: users-modify
Name: "{app}\media\photos";       Permissions: users-modify
Name: "{app}\backups";            Permissions: users-modify
Name: "{app}\staticfiles";        Permissions: users-modify
Name: "{app}\data";               Permissions: users-modify

[Icons]
; Bureau
Name: "{autodesktop}\GestionnaireRH"; Filename: "{app}\GestionnaireRH.exe"; WorkingDir: "{app}"; IconFilename: "{app}\logo.ico"; Comment: "GestionnaireRH - Gestion des Ressources Humaines"; Tasks: desktopicon

; Menu Démarrer
Name: "{group}\GestionnaireRH";                       Filename: "{app}\GestionnaireRH.exe";         WorkingDir: "{app}"; IconFilename: "{app}\logo.ico"; Comment: "Démarrer GestionnaireRH"
Name: "{group}\Arrêter GestionnaireRH";               Filename: "{app}\Arreter_GestionnaireRH.bat"; WorkingDir: "{app}"; Comment: "Arrêter le serveur GestionnaireRH"
Name: "{group}\{cm:UninstallProgram,GestionnaireRH}"; Filename: "{uninstallexe}"

; Démarrage automatique (optionnel)
Name: "{userstartup}\GestionnaireRH"; Filename: "{app}\GestionnaireRH.exe"; WorkingDir: "{app}"; Tasks: autostart

[Registry]
; Enregistrement pour le panneau "Programmes et fonctionnalités"
Root: HKCU; Subkey: "Software\Guinée RH\GestionnaireRH"; ValueType: string; ValueName: "Version";    ValueData: "1.0.0"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Guinée RH\GestionnaireRH"; ValueType: string; ValueName: "InstallDir"; ValueData: "{app}";  Flags: uninsdeletevalue

[Run]
; Proposer de lancer l'application après installation
Filename: "{app}\GestionnaireRH.exe"; Description: "Démarrer GestionnaireRH maintenant"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Arrêter le serveur avant la désinstallation
Filename: "taskkill"; Parameters: "/F /IM GestionnaireRH.exe"; Flags: runhidden; RunOnceId: "KillServer"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\staticfiles"
Type: filesandordirs; Name: "{app}\__pycache__"
Type: files;          Name: "{app}\.secret_key"
Type: files;          Name: "{app}\.trial_start"
Type: files;          Name: "{app}\install_path.txt"

[Messages]
WelcomeLabel1=Bienvenue dans l'assistant d'installation de GestionnaireRH
WelcomeLabel2=Ce programme va installer GestionnaireRH - Système de Gestion des Ressources Humaines sur votre ordinateur.%n%nGestionnaireRH est une solution complète de gestion RH développée par Guinée RH. Elle fonctionne entièrement hors ligne.%n%nFermez toutes les autres applications avant de continuer.
FinishedHeadingLabel=Installation de GestionnaireRH terminée !
FinishedLabel=GestionnaireRH a été installé avec succès sur votre ordinateur.%n%nIdentifiants par défaut :%n  Utilisateur : admin%n  Mot de passe  : admin1234%n%nL'application s'ouvre dans votre navigateur sur http://127.0.0.1:8000%n%nNOTE : Une période d'essai de 30 jours est incluse. Pour activer votre licence permanente, contactez Guinée RH.

[Code]

// ── Vérifier si l'application est en cours d'exécution ────────────────────────
function IsAppRunning(): Boolean;
var
  ResultCode: Integer;
begin
  Result := False;
  // findstr retourne 0 si trouvé, 1 si non trouvé (contrairement à tasklist seul qui retourne toujours 0)
  if Exec('cmd.exe', '/C tasklist /FI "IMAGENAME eq GestionnaireRH.exe" /NH | findstr /I "GestionnaireRH.exe"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    Result := (ResultCode = 0);
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  if IsAppRunning() then
  begin
    MsgBox(
      'GestionnaireRH est actuellement en cours d''exécution.' + #13#10 +
      'Veuillez fermer l''application avant de continuer l''installation.',
      mbError, MB_OK
    );
    Result := False;
  end;
end;

// ── Afficher l'ID machine à la fin pour l'activation ─────────────────────────
function GetMachineId(): String;
var
  MachineGuid: String;
begin
  if RegQueryStringValue(HKEY_LOCAL_MACHINE,
    'SOFTWARE\Microsoft\Cryptography', 'MachineGuid', MachineGuid) then
    Result := MachineGuid
  else
    Result := 'Indisponible';
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  // Rien ici — placeholder pour extensions futures
end;

// ── Sauvegarde de la base de données avant désinstallation ───────────────────
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DbPath:     String;
  BackupDir:  String;
  BackupPath: String;
begin
  if CurUninstallStep = usUninstall then
  begin
    DbPath := ExpandConstant('{app}\db.sqlite3');
    if FileExists(DbPath) then
    begin
      if MsgBox(
        'Voulez-vous sauvegarder votre base de données avant la désinstallation ?' + #13#10 + #13#10 +
        'La sauvegarde sera placée dans :' + #13#10 +
        ExpandConstant('{userdocs}\GestionnaireRH_Backup'),
        mbConfirmation, MB_YESNO
      ) = IDYES then
      begin
        BackupDir  := ExpandConstant('{userdocs}\GestionnaireRH_Backup');
        ForceDirectories(BackupDir);
        BackupPath := BackupDir + '\db_backup_' +
                      GetDateTimeString('yyyymmdd_hhnnss', #0, #0) + '.sqlite3';
        FileCopy(DbPath, BackupPath, False);
        MsgBox(
          'Base de données sauvegardée dans :' + #13#10 + BackupPath,
          mbInformation, MB_OK
        );
      end;
    end;
  end;
end;

// ── Créer les dossiers nécessaires après installation ────────────────────────
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    ForceDirectories(ExpandConstant('{app}\logs'));
    ForceDirectories(ExpandConstant('{app}\media'));
    ForceDirectories(ExpandConstant('{app}\backups'));
    ForceDirectories(ExpandConstant('{app}\data'));
  end;
end;

// ── Message récapitulatif avec infos licence ──────────────────────────────────
function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo,
  MemoTypeInfo, MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
begin
  Result := MemoDirInfo + NewLine + NewLine +
            MemoGroupInfo + NewLine + NewLine +
            MemoTasksInfo + NewLine + NewLine +
            '─────────────────────────────────────────' + NewLine +
            'ACTIVATION DE LICENCE' + NewLine +
            'Une période d''essai de 30 jours démarre automatiquement.' + NewLine +
            'Pour activer votre licence permanente, notez votre ID Machine' + NewLine +
            'et contactez Guinée RH.' + NewLine +
            '─────────────────────────────────────────';
end;
