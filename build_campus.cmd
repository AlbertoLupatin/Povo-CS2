@echo off
setlocal
if not exist "%~dp0.venv\Scripts\python.exe" (
  echo First run: py -3 -m venv .venv
  echo Then: .venv\Scripts\python.exe -m pip install -r requirements-build.txt
  exit /b 1
)
"%~dp0.venv\Scripts\python.exe" "%~dp0tools\build_on_windows.py" %*
exit /b %errorlevel%
