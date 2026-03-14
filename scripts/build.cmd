
@echo off
setlocal
set PYINSTALLER=.venv\Scripts\pyinstaller.exe
if not exist "%PYINSTALLER%" (
  echo PyInstaller not found. Run setup-env first.
  exit /b 1
)
"%PYINSTALLER%" --onefile --name app src/main.py --add-data "res;res"
