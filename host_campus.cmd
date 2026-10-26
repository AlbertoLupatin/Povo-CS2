@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\host_povo_campus.ps1" %*
if errorlevel 1 pause
