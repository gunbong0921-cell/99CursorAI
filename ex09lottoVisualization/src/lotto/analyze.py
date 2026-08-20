from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

import pandas as pd

NUMBER_COLS = ("n1", "n2", "n3", "n4", "n5", "n6")
ALL_NUMBERS = tuple(range(1, 46))


@dataclass(frozen=True)
class Period:
    """분석 기간. last_n과 start/end를 같이 주면 구간을 먼저 자른 뒤 최근 N회를 취한다."""

    last_n: int | None = None
    start: int | None = None
    end: int | None = None


def load_draws(db_path: Path) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    try:
        return pd.read_sql_query(
            """
            SELECT draw_no, draw_date, n1, n2, n3, n4, n5, n6, bonus, tot_sell_amount
            FROM draws
            ORDER BY draw_no
            """,
            conn,
        )
    finally:
        conn.close()


def load_prizes(db_path: Path) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    try:
        return pd.read_sql_query(
            """
            SELECT draw_no, rank, winner_count, win_amount, sum_win_amount
            FROM prizes
            ORDER BY draw_no, rank
            """,
            conn,
        )
    finally:
        conn.close()


def load_tables(db_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    return load_draws(db_path), load_prizes(db_path)


def load_db_meta(db_path: Path) -> dict[str, int | str | None]:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT MIN(draw_no), MAX(draw_no), COUNT(*), MAX(collected_at) FROM draws"
        ).fetchone()
        return {
            "min_draw": row[0],
            "max_draw": row[1],
            "count": int(row[2] or 0),
            "collected_at": row[3],
        }
    finally:
        conn.close()


def apply_period(draws: pd.DataFrame, period: Period | None = None) -> pd.DataFrame:
    df = draws.sort_values("draw_no").copy()
    if period is None:
        return df.reset_index(drop=True)
    if period.start is not None:
        df = df[df["draw_no"] >= period.start]
    if period.end is not None:
        df = df[df["draw_no"] <= period.end]
    if period.last_n is not None:
        df = df.tail(period.last_n)
    return df.reset_index(drop=True)


def _melt_numbers(draws: pd.DataFrame, *, include_bonus: bool) -> pd.Series:
    parts = [draws[col] for col in NUMBER_COLS]
    if include_bonus:
        parts.append(draws["bonus"])
    return pd.concat(parts, ignore_index=True)


def number_frequency(draws: pd.DataFrame, *, include_bonus: bool = False) -> pd.DataFrame:
    """A-01 번호 1~45 출현 횟수·비율."""
    if draws.empty:
        return pd.DataFrame(columns=["number", "count", "ratio"])
    series = _melt_numbers(draws, include_bonus=include_bonus)
    counts = series.value_counts().reindex(ALL_NUMBERS, fill_value=0)
    total = int(counts.sum())
    out = pd.DataFrame(
        {
            "number": ALL_NUMBERS,
            "count": counts.to_numpy(),
            "ratio": (counts / total).to_numpy() if total else 0.0,
        }
    )
    return out.sort_values("number").reset_index(drop=True)


def frequency_grid(freq: pd.DataFrame, rows: int = 5, cols: int = 9) -> pd.DataFrame:
    """1~45를 5x9 격자로 펼친 히트맵용 테이블."""
    grid = freq.set_index("number")["count"].reindex(ALL_NUMBERS, fill_value=0).to_numpy().reshape(rows, cols)
    return pd.DataFrame(grid, index=[f"r{i}" for i in range(1, rows + 1)], columns=list(range(1, cols + 1)))


def hot_cold(
    draws: pd.DataFrame,
    *,
    top_k: int = 5,
    include_bonus: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """A-02 핫(상위)·콜드(하위) 번호. 기간은 호출 전 apply_period로 자른다."""
    freq = number_frequency(draws, include_bonus=include_bonus)
    ordered = freq.sort_values(["count", "number"], ascending=[False, True])
    hot = ordered.head(top_k).reset_index(drop=True)
    cold = ordered.sort_values(["count", "number"], ascending=[True, True]).head(top_k).reset_index(drop=True)
    return hot, cold


def odd_even_and_sum(draws: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """A-03 회차별 홀짝·합계, 홀짝 패턴 분포, 합계 분포."""
    if draws.empty:
        empty = pd.DataFrame()
        return empty, empty, empty
    nums = draws[list(NUMBER_COLS)]
    odd = (nums % 2 == 1).sum(axis=1)
    even = 6 - odd
    total = nums.sum(axis=1)
    per_draw = pd.DataFrame(
        {
            "draw_no": draws["draw_no"].to_numpy(),
            "draw_date": draws["draw_date"].to_numpy(),
            "odd_count": odd.to_numpy(),
            "even_count": even.to_numpy(),
            "number_sum": total.to_numpy(),
        }
    )
    pattern = (
        per_draw.groupby(["odd_count", "even_count"], as_index=False)
        .size()
        .rename(columns={"size": "draw_count"})
        .sort_values("draw_count", ascending=False)
        .reset_index(drop=True)
    )
    pattern["ratio"] = pattern["draw_count"] / len(per_draw)
    sum_dist = (
        per_draw["number_sum"]
        .value_counts()
        .sort_index()
        .rename_axis("number_sum")
        .reset_index(name="draw_count")
    )
    sum_dist["ratio"] = sum_dist["draw_count"] / len(per_draw)
    return per_draw, pattern, sum_dist


def consecutive_stats(draws: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """A-04 같은 회차 연속번호(차이 1) 집계."""
    rows: list[dict[str, int]] = []
    pair_rows: list[tuple[int, int]] = []
    for rec in draws.itertuples(index=False):
        nums = sorted(int(getattr(rec, col)) for col in NUMBER_COLS)
        pairs = [(nums[i], nums[i + 1]) for i in range(5) if nums[i + 1] - nums[i] == 1]
        rows.append({"draw_no": int(rec.draw_no), "consecutive_pair_count": len(pairs)})
        pair_rows.extend(pairs)
    per_draw = pd.DataFrame(rows)
    if pair_rows:
        pair_df = pd.DataFrame(pair_rows, columns=["low", "high"])
        pair_df["label"] = pair_df["low"].astype(str) + "-" + pair_df["high"].astype(str)
        pair_freq = (
            pair_df.groupby(["low", "high", "label"], as_index=False)
            .size()
            .rename(columns={"size": "count"})
            .sort_values(["count", "low"], ascending=[False, True])
            .reset_index(drop=True)
        )
    else:
        pair_freq = pd.DataFrame(columns=["low", "high", "label", "count"])
    return per_draw, pair_freq


def number_pairs(draws: pd.DataFrame, *, top_k: int = 20) -> pd.DataFrame:
    """A-05 같은 회차 번호쌍 빈도 상위 K."""
    counter: dict[tuple[int, int], int] = {}
    for rec in draws.itertuples(index=False):
        nums = sorted(int(getattr(rec, col)) for col in NUMBER_COLS)
        for a, b in combinations(nums, 2):
            counter[(a, b)] = counter.get((a, b), 0) + 1
    if not counter:
        return pd.DataFrame(columns=["a", "b", "label", "count"])
    items = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0][0], kv[0][1]))[:top_k]
    return pd.DataFrame(
        {
            "a": [k[0] for k, _ in items],
            "b": [k[1] for k, _ in items],
            "label": [f"{k[0]}-{k[1]}" for k, _ in items],
            "count": [v for _, v in items],
        }
    )


def bonus_frequency(draws: pd.DataFrame) -> pd.DataFrame:
    """A-06 보너스 번호 출현 빈도."""
    if draws.empty:
        return pd.DataFrame(columns=["number", "count", "ratio"])
    counts = draws["bonus"].value_counts().reindex(ALL_NUMBERS, fill_value=0)
    total = int(counts.sum())
    return pd.DataFrame(
        {
            "number": ALL_NUMBERS,
            "count": counts.to_numpy(),
            "ratio": (counts / total).to_numpy() if total else 0.0,
        }
    )


def prize_trend(prizes: pd.DataFrame, draws: pd.DataFrame, *, rank: int | None = None) -> pd.DataFrame:
    """A-07 등수별 당첨금·당첨자 수 추이."""
    if prizes.empty or draws.empty:
        return pd.DataFrame(columns=["draw_no", "draw_date", "rank", "winner_count", "win_amount", "sum_win_amount"])
    scoped = prizes[prizes["draw_no"].isin(draws["draw_no"])].copy()
    if rank is not None:
        scoped = scoped[scoped["rank"] == rank]
    dates = draws[["draw_no", "draw_date"]]
    merged = scoped.merge(dates, on="draw_no", how="left")
    return merged.sort_values(["draw_no", "rank"]).reset_index(drop=True)[
        ["draw_no", "draw_date", "rank", "winner_count", "win_amount", "sum_win_amount"]
    ]


def lookup_draw(draws: pd.DataFrame, prizes: pd.DataFrame, draw_no: int) -> tuple[pd.Series | None, pd.DataFrame]:
    """회차별 조회용. Part 3에서도 사용."""
    hit = draws[draws["draw_no"] == draw_no]
    if hit.empty:
        return None, pd.DataFrame()
    prize_rows = prizes[prizes["draw_no"] == draw_no].sort_values("rank").reset_index(drop=True)
    return hit.iloc[0], prize_rows


def search_by_numbers(draws: pd.DataFrame, numbers: list[int]) -> pd.DataFrame:
    """선택한 번호가 본번호에 모두 포함된 회차."""
    if not numbers:
        return draws.copy()
    mask = pd.Series(True, index=draws.index)
    for n in numbers:
        mask &= draws[list(NUMBER_COLS)].eq(n).any(axis=1)
    return draws.loc[mask].reset_index(drop=True)


def period_meta(draws: pd.DataFrame) -> dict[str, int | str | None]:
    if draws.empty:
        return {"count": 0, "min_draw": None, "max_draw": None, "start_date": None, "end_date": None}
    return {
        "count": int(len(draws)),
        "min_draw": int(draws["draw_no"].min()),
        "max_draw": int(draws["draw_no"].max()),
        "start_date": str(draws["draw_date"].min()),
        "end_date": str(draws["draw_date"].max()),
    }


@dataclass
class AnalysisBundle:
    meta: dict[str, int | str | None]
    frequency: pd.DataFrame
    frequency_with_bonus: pd.DataFrame
    hot: pd.DataFrame
    cold: pd.DataFrame
    odd_even_draws: pd.DataFrame
    odd_even_pattern: pd.DataFrame
    sum_dist: pd.DataFrame
    consecutive_draws: pd.DataFrame
    consecutive_pairs: pd.DataFrame
    pairs: pd.DataFrame
    bonus: pd.DataFrame
    prizes: pd.DataFrame


def analyze(
    db_path: Path,
    *,
    period: Period | None = None,
    pair_top_k: int = 20,
    hot_k: int = 5,
) -> AnalysisBundle:
    draws_all, prizes_all = load_tables(db_path)
    draws = apply_period(draws_all, period)
    freq = number_frequency(draws, include_bonus=False)
    hot, cold = hot_cold(draws, top_k=hot_k, include_bonus=False)
    odd_draws, odd_pattern, sum_dist = odd_even_and_sum(draws)
    cons_draws, cons_pairs = consecutive_stats(draws)
    return AnalysisBundle(
        meta=period_meta(draws),
        frequency=freq,
        frequency_with_bonus=number_frequency(draws, include_bonus=True),
        hot=hot,
        cold=cold,
        odd_even_draws=odd_draws,
        odd_even_pattern=odd_pattern,
        sum_dist=sum_dist,
        consecutive_draws=cons_draws,
        consecutive_pairs=cons_pairs,
        pairs=number_pairs(draws, top_k=pair_top_k),
        bonus=bonus_frequency(draws),
        prizes=prize_trend(prizes_all, draws),
    )
