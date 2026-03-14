
        #!/usr/bin/env bash
        set -euo pipefail
        python3 -m venv .venv
        source .venv/bin/activate
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
        if [ -s requirements.txt ]; then pip install -r requirements.txt; fi
        printf "
[OK] .venv ready.
"
