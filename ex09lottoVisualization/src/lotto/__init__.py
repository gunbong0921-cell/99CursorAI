"""로또 6/45 수집·분석 패키지."""

__all__ = ["ROOT_DIR", "DATA_DIR"]

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "lotto.db"
