
$ErrorActionPreference = 'Stop'
python -m venv .venv
& ./.venv/Scripts/Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
if (Test-Path requirements.txt) { if ((Get-Content requirements.txt).Length -gt 0) { pip install -r requirements.txt } }
Write-Host "`n[OK] .venv ready."
