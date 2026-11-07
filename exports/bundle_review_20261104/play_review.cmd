@echo off
setlocal
tasklist /FI "IMAGENAME eq cs2.exe" /NH | find /I "cs2.exe" >nul
if not errorlevel 1 (
  echo CS2 is already running. Close it before reopening the bundle review.
  pause
  exit /b 1
)
start "" /D "C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\bin\win64" "C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\bin\win64\cs2.exe" -steam -retail -addon trento_povo_bundle_review -tools -insecure -condebug -vconsole -netconport 27400 +game_type 0 +game_mode 2 +map maps/trento_povo_campus.vpk +bot_quota 0 +mp_warmup_pausetimer 1
"%~dp0..\..\.venv\Scripts\python.exe" "%~dp0..\..\tools\cs2_explore.py" --map trento_povo_campus --timeout 120 --fly
