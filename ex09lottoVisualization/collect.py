"""동행복권 로또 6/45 당첨결과 수집 진입점.

사용:
  .venv\\Scripts\\python.exe collect.py
  .venv\\Scripts\\python.exe collect.py --retry-failed
  .venv\\Scripts\\python.exe collect.py --rounds 1,2,10-12
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from lotto.pipeline import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
