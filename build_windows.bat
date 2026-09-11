@echo off
setlocal
cd /d "%~dp0"

echo =============================================
echo  Forensic CV Manager - SemVer Portable Builder
echo =============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python was not found on PATH.
    echo Install Python and select "Add Python to PATH", then try again.
    pause
    exit /b 1
)

echo [1/7] Installing required packages...
python -m pip install --upgrade pip
if errorlevel 1 goto :build_failed
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto :build_failed


echo [2/7] Generating version metadata...
python build_metadata.py
if errorlevel 1 goto :build_failed

echo [3/7] Creating sanitized release template...
python create_release_template.py
if errorlevel 1 goto :build_failed

echo [4/7] Creating Windows executable...
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "ForensicCVManager" --version-file "version_info.txt" --icon "assets\app.ico" --add-data "assets;assets" app.py
if errorlevel 1 goto :build_failed

echo [5/7] Preparing portable release folder...
if not exist "dist\data" mkdir "dist\data"
if not exist "dist\Resume" mkdir "dist\Resume"
if not exist "dist\Backups" mkdir "dist\Backups"
copy /Y "data\template.sqlite3" "dist\data\template.sqlite3" >nul
copy /Y "README.md" "dist\README.txt" >nul
copy /Y "Sample_Generated_CV.docx" "dist\Sample_Generated_CV.docx" >nul
copy /Y "Sample_Generated_CV.pdf" "dist\Sample_Generated_CV.pdf" >nul
copy /Y "USER_MANUAL.md" "dist\USER_MANUAL.txt" >nul
copy /Y "LICENSE" "dist\LICENSE.txt" >nul

rem Optional Authenticode signing. Set SIGN_PFX and SIGN_PASSWORD before building.
echo [6/7] Checking code-signing configuration...
if defined SIGN_PFX (
    where signtool >nul 2>nul
    if errorlevel 1 (
        echo WARNING: SIGN_PFX is set, but signtool.exe was not found. Executable remains unsigned.
    ) else (
        signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /f "%SIGN_PFX%" /p "%SIGN_PASSWORD%" "dist\ForensicCVManager.exe"
        if errorlevel 1 goto :build_failed
        echo Executable signed successfully.
    )
) else (
    echo No signing certificate configured. The executable will show Unknown Publisher.
)

echo [7/7] Build complete.
echo Portable folder: "%~dp0dist"
echo.
echo Copy the entire dist folder to the flash drive.
echo Run build_installer.bat afterward if Inno Setup is installed and an installer is needed.
pause
exit /b 0

:build_failed
echo.
echo Build failed. Review the error messages above.
pause
exit /b 1
