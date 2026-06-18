"""Make ``import reelpath`` work during tests without requiring an install.

Putting ``src`` on ``sys.path`` here means ``pytest`` runs straight from a clean
checkout (``pip install -r requirements.txt`` then ``pytest -q``), while an
editable install (``pip install -e .``) keeps working too.
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
