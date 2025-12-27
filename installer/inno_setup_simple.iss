; Script Inno Setup pour GestionnaireRH
#define MyAppName "GestionnaireRH"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Guinee RH"
#define SourceDir "C:\Users\LENO\Desktop\GestionnaireRH"

[Setup]
AppId={{B2C3D4E5-F6A7-8901-BCDE-F12345678901}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=output
OutputBaseFilename=GestionnaireRH_Setup
Compression=lzma
WizardStyle=modern
PrivilegesRequired=lowest

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Creer un raccourci sur le Bureau"; Flags: checkedonce

[Files]
Source: "{#SourceDir}\*.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\gestionnaire_rh\*"; DestDir: "{app}\gestionnaire_rh"; Flags: ignoreversion recursesubdirs
Source: "{#SourceDir}\core\*"; DestDir: "{app}\core"; Flags: ignoreversion recursesubdirs; Excludes: "__pycache__"
Source: "{#SourceDir}\employes\*"; DestDir: "{app}\employes"; Flags: ignoreversion recursesubdirs; Excludes: "__pycache__"
Source: "{#SourceDir}\paie\*"; DestDir: "{app}\paie"; Flags: ignoreversion recursesubdirs; Excludes: "__pycache__"
Source: "{#SourceDir}\temps_travail\*"; DestDir: "{app}\temps_travail"; Flags: ignoreversion recursesubdirs; Excludes: "__pycache__"
Source: "{#SourceDir}\recrutement\*"; DestDir: "{app}\recrutement"; Flags: ignoreversion recursesubdirs; Excludes: "__pycache__"
Source: "{#SourceDir}\formation\*"; DestDir: "{app}\formation"; Flags: ignoreversion recursesubdirs; Excludes: "__pycache__"
Source: "{#SourceDir}\dashboard\*"; DestDir: "{app}\dashboard"; Flags: ignoreversion recursesubdirs; Excludes: "__pycache__"
Source: "{#SourceDir}\payments\*"; DestDir: "{app}\payments"; Flags: ignoreversion recursesubdirs; Excludes: "__pycache__"
Source: "{#SourceDir}\templates\*"; DestDir: "{app}\templates"; Flags: ignoreversion recursesubdirs
Source: "{#SourceDir}\static\*"; DestDir: "{app}\static"; Flags: ignoreversion recursesubdirs
Source: "{#SourceDir}\staticfiles\*"; DestDir: "{app}\staticfiles"; Flags: ignoreversion recursesubdirs skipifsourcedoesntexist
Source: "{#SourceDir}\installer\portable\*.bat"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\logs"
Name: "{app}\media"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\lancer_gestionnaire_rh.bat"; WorkingDir: "{app}"
Name: "{group}\Premier Demarrage"; Filename: "{app}\premier_demarrage.bat"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\lancer_gestionnaire_rh.bat"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\premier_demarrage.bat"; Description: "Installation initiale"; WorkingDir: "{app}"; Flags: nowait postinstall shellexec
