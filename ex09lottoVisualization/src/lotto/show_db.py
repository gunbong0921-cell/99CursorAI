"""lotto.db 요약 조회."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / "data" / "lotto.db"


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    print(f"DB: {DB}")
    print("tables:", [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")])
    mn, mx, cnt = conn.execute("SELECT MIN(draw_no), MAX(draw_no), COUNT(*) FROM draws").fetchone()
    print(f"draws: {cnt} rows, {mn}~{mx}회")
    print(f"prizes: {conn.execute('SELECT COUNT(*) FROM prizes').fetchone()[0]} rows")
    print("latest 5 draws:")
    for row in conn.execute(
        "SELECT draw_no, draw_date, n1, n2, n3, n4, n5, n6, bonus FROM draws ORDER BY draw_no DESC LIMIT 5"
    ):
        nums = [row["n1"], row["n2"], row["n3"], row["n4"], row["n5"], row["n6"]]
        print(f"  {row['draw_no']}회 {row['draw_date']}  {nums}  bonus {row['bonus']}")
    latest = mx
    print(f"{latest}회 prizes:")
    for row in conn.execute(
        "SELECT rank, winner_count, win_amount FROM prizes WHERE draw_no=? ORDER BY rank",
        (latest,),
    ):
        print(f"  {row['rank']}등  winners={row['winner_count']:,}  amount={row['win_amount']:,}")
    conn.close()


if __name__ == "__main__":
    main()
