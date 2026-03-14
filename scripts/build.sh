
#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
pyinstaller --onefile --name app src/main.py --add-data "res:res"
