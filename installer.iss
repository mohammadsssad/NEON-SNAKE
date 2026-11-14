[Setup]
AppId={{A91B7C32-4F21-49E8-9D31-AB12CDE45678}
AppName=NEON SNAKE
AppVersion=1.0.0
DefaultDirName={autopf}\NEON SNAKE
DefaultGroupName=NEON SNAKE
OutputDir=dist-installer
OutputBaseFilename=NEON_SNAKE_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Files]
Source: "dist\NEON_SNAKE.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\NEON SNAKE"; Filename: "{app}\NEON_SNAKE.exe"
Name: "{autodesktop}\NEON SNAKE"; Filename: "{app}\NEON_SNAKE.exe"
