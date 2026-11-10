@echo off
title Sync MaTech Android Tool to GitHub
cd /d "%~dp0"
echo ========================================================
echo   Syncing MaTech Android Tool to GitHub
echo   Repository: macvollan/matech-android-tool
echo ========================================================
python auto_sync_github.py %*
pause
