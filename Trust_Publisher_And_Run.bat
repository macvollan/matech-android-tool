@echo off
title MacTech Android Tool - Verified Publisher Trust & Launch
cd /d "%~dp0"
echo ========================================================
echo   MacTech Android Tool - Verified Publisher Trust
echo   MacTech Solutions Lab Enterprise Forensics
echo ========================================================
echo.
echo [1/3] Removing Internet Mark-of-the-Web (MOTW) download flags...
powershell -NoProfile -Command "Get-ChildItem -Path '%~dp0' -Recurse | Unblock-File -ErrorAction SilentlyContinue"

echo [2/3] Registering MacTech Solutions Lab certificate as Trusted Publisher...
if exist "MacTech_Solutions_Lab.cer" (
    certutil -addstore -user -f "TrustedPublisher" "%~dp0MacTech_Solutions_Lab.cer" >nul 2>&1
)

echo [3/3] Launching MacTech Android Tool...
echo.
start "" "%~dp0MacTech_Android_Tool.exe"
exit
