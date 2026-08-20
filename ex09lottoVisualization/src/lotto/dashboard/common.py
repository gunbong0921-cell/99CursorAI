from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from lotto import DEFAULT_DB_PATH
from lotto.analyze import Period, apply_period, load_db_meta, load_tables, period_meta

DISCLAIMER = (
    "이 화면의 통계는 동행복권 공개 당첨결과를 재가공한 과거 데이터 분석입니다. "
    "번호 출현 빈도는 미래 당첨을 의미하거나 보장하지 않습니다."
)
SOURCE = "데이터 출처: 동행복권 (dhlottery.co.kr)"


def db_path() -> Path:
    return DEFAULT_DB_PATH


def require_db() -> bool:
    path = db_path()
    if not path.exists():
        st.error("SQLite 파일이 없습니다. 프로젝트 루트에서 `python collect.py`를 먼저 실행하세요.")
        return False
    return True


@st.cache_data(show_spinner="데이터를 불러오는 중...")
def cached_tables(db_file: str, mtime: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    _ = mtime
    return load_tables(Path(db_file))


def get_tables() -> tuple[pd.DataFrame, pd.DataFrame] | None:
    path = db_path()
    if not path.exists():
        return None
    return cached_tables(str(path), path.stat().st_mtime)


def render_sidebar(draws: pd.DataFrame | None = None) -> Period:
    st.sidebar.header("분석 기간")
    path = db_path()
    if path.exists():
        meta = load_db_meta(path)
        st.sidebar.caption(
            f"DB {meta['min_draw']}~{meta['max_draw']}회 · {meta['count']}건"
        )
        if meta["collected_at"]:
            st.sidebar.caption(f"수집 시각(UTC): {meta['collected_at']}")
    mode = st.sidebar.radio("기간 방식", ["전체", "최근 N회", "회차 구간"], index=0)
    last_n = start = end = None
    if draws is not None and not draws.empty:
        mn, mx = int(draws["draw_no"].min()), int(draws["draw_no"].max())
    else:
        mn, mx = 1, 1
    if mode == "최근 N회":
        last_n = st.sidebar.slider("최근 N회", min_value=10, max_value=min(300, mx), value=min(50, mx), step=1)
    elif mode == "회차 구간":
        start, end = st.sidebar.slider("회차 구간", min_value=mn, max_value=mx, value=(mn, mx))
    st.sidebar.info("데이터 갱신: 터미널에서 `python collect.py`")
    st.sidebar.caption(SOURCE)
    return Period(last_n=last_n, start=start, end=end)


def scoped_draws(draws: pd.DataFrame, period: Period) -> pd.DataFrame:
    scoped = apply_period(draws, period)
    meta = period_meta(scoped)
    st.caption(
        f"분석 구간: {meta['min_draw']}~{meta['max_draw']}회 "
        f"({meta['start_date']} ~ {meta['end_date']}) · {meta['count']}회차"
    )
    return scoped


def footer() -> None:
    st.divider()
    st.caption(f"{SOURCE}  |  {DISCLAIMER}")


def ball_color(number: int) -> str:
    if number <= 10:
        return "#fbc400"
    if number <= 20:
        return "#69c8f2"
    if number <= 30:
        return "#ff7272"
    if number <= 40:
        return "#aaaaaa"
    return "#b0d840"


def render_balls(numbers: list[int], bonus: int | None = None) -> None:
    chips = []
    for n in numbers:
        chips.append(
            f'<span style="display:inline-flex;width:42px;height:42px;border-radius:50%;'
            f'align-items:center;justify-content:center;margin-right:8px;font-weight:700;'
            f'background:{ball_color(int(n))};color:#222;">{int(n)}</span>'
        )
    if bonus is not None:
        chips.append('<span style="margin:0 8px;color:#666;">+</span>')
        chips.append(
            f'<span style="display:inline-flex;width:42px;height:42px;border-radius:50%;'
            f'align-items:center;justify-content:center;font-weight:700;'
            f'background:{ball_color(int(bonus))};color:#222;outline:3px solid #333;">'
            f"{int(bonus)}</span>"
        )
    st.markdown("".join(chips), unsafe_allow_html=True)


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str, x_title: str, y_title: str) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(x, title=x_title),
            y=alt.Y(y, title=y_title),
            tooltip=list(df.columns),
        )
        .properties(title=title, height=360)
    )


def line_chart(df: pd.DataFrame, x: str, y: str, title: str, x_title: str, y_title: str) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X(x, title=x_title),
            y=alt.Y(y, title=y_title),
            tooltip=list(df.columns),
        )
        .properties(title=title, height=360)
    )
