@echo off
setlocal
cd /d "%~dp0"

set "ISCC="

rem Check PATH first
for /f "delims=" %%I in ('where ISCC.exe 2^>nul') do (
    if not defined ISCC set "ISCC=%%I"
)

rem Standard 32-bit Program Files location
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
)

rem Standard 64-bit Program Files location
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
)

rem Per-user installation
if not defined ISCC if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
    set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
)

if not defined ISCC (
    echo.
    echo Inno Setup 6 was found by neither PATH nor the standard install locations.
    echo.
    echo Please verify that ISCC.exe is installed.
    pause
    exit /b 1
)

echo Using Inno Setup:
echo "%ISCC%"
echo.

python build_metadata.py
if errorlevel 1 goto :failed

if not exist "dist\ForensicCVManager.exe" (
    echo Build the portable application first with build_windows.bat.
    pause
    exit /b 1
)

"%ISCC%" ForensicCVManager.iss
if errorlevel 1 goto :failed

echo.
echo Installer created in the installer folder.
pause
exit /b 0

:failed
echo Installer build failed.
pause
exit /b 1
