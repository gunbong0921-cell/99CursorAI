"""로또 6/45 통계 분석 진입점 (Part 2).

사용:
  .venv\\Scripts\\python.exe analyze.py
  .venv\\Scripts\\python.exe analyze.py --last 50
  .venv\\Scripts\\python.exe analyze.py --start 1000 --end 1237
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

from lotto.analyze_cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
