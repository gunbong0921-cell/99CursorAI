from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from . import DEFAULT_DB_PATH
from .analyze import Period, analyze


def _print_section(title: str) -> None:
    print()
    print(f"== {title} ==")


def _print_df(df: pd.DataFrame, *, max_rows: int = 15) -> None:
    if df.empty:
        print("(없음)")
        return
    with pd.option_context("display.max_rows", max_rows, "display.width", 120, "display.float_format", "{:.4f}".format):
        print(df.head(max_rows).to_string(index=False))
        if len(df) > max_rows:
            print(f"... 외 {len(df) - max_rows}행")


def run_report(
    db_path: Path,
    *,
    last_n: int | None,
    start: int | None,
    end: int | None,
    pair_top_k: int,
    hot_k: int,
    include_bonus_freq: bool,
) -> int:
    if not db_path.exists():
        print(f"DB가 없습니다: {db_path}")
        print("먼저 collect.py를 실행하세요.")
        return 1
    bundle = analyze(
        db_path,
        period=Period(last_n=last_n, start=start, end=end),
        pair_top_k=pair_top_k,
        hot_k=hot_k,
    )
    meta = bundle.meta
    print(
        f"기간: {meta['min_draw']}~{meta['max_draw']}회 "
        f"({meta['start_date']} ~ {meta['end_date']}), {meta['count']}회차"
    )

    _print_section("A-01 번호 출현 빈도 (본번호, 상위 10)")
    freq = bundle.frequency.sort_values("count", ascending=False)
    _print_df(freq.head(10), max_rows=10)
    if include_bonus_freq:
        _print_section("A-01 번호 출현 빈도 (보너스 포함, 상위 10)")
        _print_df(bundle.frequency_with_bonus.sort_values("count", ascending=False).head(10), max_rows=10)

    _print_section(f"A-02 핫 번호 상위 {hot_k}")
    _print_df(bundle.hot, max_rows=hot_k)
    _print_section(f"A-02 콜드 번호 하위 {hot_k}")
    _print_df(bundle.cold, max_rows=hot_k)

    _print_section("A-03 홀짝 패턴")
    _print_df(bundle.odd_even_pattern, max_rows=7)
    if not bundle.odd_even_draws.empty:
        sums = bundle.odd_even_draws["number_sum"]
        print(
            f"합계: min={int(sums.min())} median={sums.median():.1f} "
            f"mean={sums.mean():.1f} max={int(sums.max())}"
        )

    _print_section("A-04 연속번호 쌍 (상위 10)")
    _print_df(bundle.consecutive_pairs.head(10), max_rows=10)
    if not bundle.consecutive_draws.empty:
        c = bundle.consecutive_draws["consecutive_pair_count"]
        print(
            f"회차별 연속쌍 수: 0개 {(c == 0).sum()}회 / "
            f"1개 이상 {(c >= 1).sum()}회 / 평균 {c.mean():.2f}"
        )

    _print_section(f"A-05 번호쌍 상위 {pair_top_k}")
    _print_df(bundle.pairs, max_rows=pair_top_k)

    _print_section("A-06 보너스 빈도 상위 10")
    _print_df(bundle.bonus.sort_values("count", ascending=False).head(10), max_rows=10)

    _print_section("A-07 등수별 당첨 추이 (최근 5회, 1등)")
    first = bundle.prizes[bundle.prizes["rank"] == 1].tail(5)
    _print_df(first, max_rows=5)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="로또 6/45 SQLite 데이터 통계 분석 (Part 2)")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--last", type=int, default=None, help="최근 N회만")
    parser.add_argument("--start", type=int, default=None, help="시작 회차")
    parser.add_argument("--end", type=int, default=None, help="끝 회차")
    parser.add_argument("--top", type=int, default=20, help="번호쌍 상위 K")
    parser.add_argument("--hot-k", type=int, default=5, help="핫/콜드 개수")
    parser.add_argument("--include-bonus", action="store_true", help="빈도 출력에 보너스 포함 버전도 표시")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run_report(
        args.db,
        last_n=args.last,
        start=args.start,
        end=args.end,
        pair_top_k=args.top,
        hot_k=args.hot_k,
        include_bonus_freq=args.include_bonus,
    )


if __name__ == "__main__":
    sys.exit(main())
