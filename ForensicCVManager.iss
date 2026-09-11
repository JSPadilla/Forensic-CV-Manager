#define MyAppName "Forensic CV Manager"
#include "installer_version.iss"
#define MyAppPublisher "Forensic CV Manager Project"
#define MyAppExeName "ForensicCVManager.exe"

[Setup]
AppId={{9F345992-3C0D-4C93-BCB6-730ED1AA355A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\Forensic CV Manager
DefaultGroupName={#MyAppName}
OutputDir=installer
OutputBaseFilename=ForensicCVManager-{#MyAppVersion}-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=assets\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
WizardImageFile=assets\installer_wizard.bmp
WizardSmallImageFile=assets\installer_small.bmp
LicenseFile=LICENSE
InfoBeforeFile=INSTALLER_WELCOME.txt
DisableProgramGroupPage=yes

[Files]
Source: "dist\ForensicCVManager.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\data\template.sqlite3"; DestDir: "{app}\data"; Flags: ignoreversion onlyifdoesntexist
Source: "dist\README.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\USER_MANUAL.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Sample_Generated_CV.docx"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Sample_Generated_CV.pdf"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\Resume"
Name: "{app}\Backups"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
