from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PrizeRecord:
    rank: int
    winner_count: int
    win_amount: int
    sum_win_amount: int | None = None


@dataclass(frozen=True)
class DrawRecord:
    draw_no: int
    draw_date: str
    numbers: tuple[int, int, int, int, int, int]
    bonus: int
    tot_sell_amount: int | None
    prizes: tuple[PrizeRecord, ...]
    source: str
