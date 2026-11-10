@echo off
title Sync MacTech Android Tool to GitHub
cd /d "%~dp0"
echo ========================================================
echo   Syncing MacTech Android Tool to GitHub
echo   Repository: macvollan/mactech-android-tool
echo ========================================================
python auto_sync_github.py %*
pause
