; Script Inno Setup pour GestionnaireRH
; Crée un installateur Windows professionnel

#define MyAppName "GestionnaireRH"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Guinée RH"
#define MyAppURL "https://www.guineerh.space"
#define MyAppExeName "GestionnaireRH.exe"

[Setup]
; Identifiant unique de l'application
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Fichier de sortie
OutputDir=output
OutputBaseFilename=GestionnaireRH_Setup_{#MyAppVersion}
; Icône de l'installateur
SetupIconFile=..\static\img\favicon.ico
; Compression
Compression=lzma2/ultra64
SolidCompression=yes
; Interface
WizardStyle=modern
; Privilèges (pas besoin d'admin pour installer dans AppData)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Langue
ShowLanguageDialog=auto

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
french.LaunchApp=Lancer {#MyAppName} maintenant
english.LaunchApp=Launch {#MyAppName} now

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Tous les fichiers de l'application PyInstaller
Source: "dist\GestionnaireRH\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Créer le dossier data
Source: "data_template\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs onlyifdoesntexist uninsneveruninstall

[Dirs]
; Dossiers avec permissions d'écriture
Name: "{app}\data"; Permissions: users-modify
Name: "{app}\data\logs"; Permissions: users-modify
Name: "{app}\data\media"; Permissions: users-modify

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "Gestionnaire RH Guinée"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Comment: "Gestionnaire RH Guinée"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchApp}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Ne pas supprimer les données utilisateur lors de la désinstallation
; Les logs peuvent être supprimés
Type: filesandordirs; Name: "{app}\data\logs"

[Code]
// Vérifier si l'application est déjà en cours d'exécution
function IsAppRunning(): Boolean;
var
  ResultCode: Integer;
begin
  Result := False;
  if Exec('tasklist', '/FI "IMAGENAME eq GestionnaireRH.exe" /NH', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    // Si le processus existe, demander de le fermer
    Result := ResultCode = 0;
  end;
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  // Vérifier si l'application est en cours d'exécution
  if IsAppRunning() then
  begin
    MsgBox('GestionnaireRH est actuellement en cours d''exécution.' + #13#10 + 
           'Veuillez fermer l''application avant de continuer l''installation.', 
           mbError, MB_OK);
    Result := False;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Créer les sous-dossiers nécessaires
    ForceDirectories(ExpandConstant('{app}\data\logs'));
    ForceDirectories(ExpandConstant('{app}\data\media'));
  end;
end;
