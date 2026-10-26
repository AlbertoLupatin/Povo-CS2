@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\play_povo_campus.ps1" -Winter %*
if errorlevel 1 pause
