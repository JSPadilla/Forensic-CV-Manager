@echo off
setlocal
cd /d "%~dp0"

rem Locate the Inno Setup compiler. Install location can vary depending on
rem whether Inno Setup was installed system-wide, per-user, or via winget.
set "ISCC="

rem Prefer ISCC.exe when it is already available on PATH.
for /f "delims=" %%I in ('where ISCC.exe 2^>nul') do (
  if not defined ISCC set "ISCC=%%I"
)

rem Standard system-wide installation locations.
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
  set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
)
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
  set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
)

rem Common per-user installation location, including winget installs.
if not defined ISCC if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
  set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
)

if not defined ISCC (
  echo.
  echo Inno Setup 6 compiler ^(ISCC.exe^) was not found.
  echo.
  echo Checked:
  echo   - PATH
  echo   - %ProgramFiles(x86)%\Inno Setup 6
  echo   - %ProgramFiles%\Inno Setup 6
  echo   - %LOCALAPPDATA%\Programs\Inno Setup 6
  echo.
  echo If Inno Setup is installed elsewhere, add its folder to PATH
  echo or update build_installer.bat with the correct ISCC.exe location.
  pause
  exit /b 1
)

echo Using Inno Setup compiler:
echo   "%ISCC%"
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
