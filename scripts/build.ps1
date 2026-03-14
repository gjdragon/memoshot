$ErrorActionPreference = 'Stop'
& ./.venv/Scripts/Activate.ps1

pyinstaller `
  --onefile `
  --name app `
  --icon "res/icon.ico" `
  --add-data "res;res" `
  src/main.py