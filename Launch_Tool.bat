@echo off
cd /d "%~dp0"
powershell -NoProfile -Command "Get-ChildItem -Path '%~dp0' -Recurse | Unblock-File -ErrorAction SilentlyContinue"
start "" "%~dp0MacTech_Android_Tool.exe"
exit
