"""Vercel Python entry point.

Vercel discovers the module-level ASGI `app` and serves it. Everything except
/assets is rewritten here by vercel.json.
"""

import sys
from pathlib import Path

# The function runs with /var/task as cwd; make the app package importable.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402

__all__ = ["app"]
