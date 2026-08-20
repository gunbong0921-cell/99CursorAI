from __future__ import annotations

import altair as alt
import streamlit as st

from lotto.analyze import (
    NUMBER_COLS,
    bonus_frequency,
    consecutive_stats,
    hot_cold,
    lookup_draw,
    number_frequency,
    number_pairs,
    odd_even_and_sum,
    prize_trend,
    search_by_numbers,
)
from lotto.dashboard.common import (
    DISCLAIMER,
    SOURCE,
    bar_chart,
    footer,
    get_tables,
    line_chart,
    render_balls,
    render_sidebar,
    require_db,
    scoped_draws,
)


def page_intro() -> None:
    st.title("로또 6/45 당첨번호 시각화")
    st.write(
        "동행복권 로또 6/45 당첨결과를 수집·저장한 뒤, 빈도·분포·당첨금 추이를 차트로 보여 주는 포트폴리오 대시보드입니다."
    )
    if not require_db():
        footer()
        return
    tables = get_tables()
    if tables is None:
        footer()
        return
    draws, prizes = tables
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("저장 회차", f"{len(draws):,}회")
    c2.metric("시작", f"{int(draws['draw_no'].min())}회")
    c3.metric("최신", f"{int(draws['draw_no'].max())}회")
    c4.metric("등수 행", f"{len(prizes):,}")
    st.subheader("구성")
    st.markdown(
        "- Part 1 수집: 공식 JSON → SQLite (`collect.py`)\n"
        "- Part 2 분석: pandas 통계 (`analyze.py`)\n"
        "- Part 3 시각화: 이 Streamlit 화면"
    )
    st.warning(DISCLAIMER)
    st.caption(SOURCE)
    footer()


def page_lookup() -> None:
    st.title("회차 조회")
    if not require_db():
        footer()
        return
    tables = get_tables()
    if tables is None:
        return
    draws, prizes = tables
    mn, mx = int(draws["draw_no"].min()), int(draws["draw_no"].max())
    draw_no = st.number_input("회차", min_value=mn, max_value=mx, value=mx, step=1)
    row, prize_rows = lookup_draw(draws, prizes, int(draw_no))
    if row is None:
        st.warning("해당 회차가 없습니다.")
        footer()
        return
    st.subheader(f"{int(row['draw_no'])}회 · {row['draw_date']}")
    nums = [int(row[c]) for c in NUMBER_COLS]
    render_balls(nums, int(row["bonus"]))
    if prize_rows.empty:
        st.info("등수 정보가 없습니다.")
    else:
        show = prize_rows.copy()
        show["등수"] = show["rank"].map(lambda r: f"{int(r)}등")
        show["당첨자 수"] = show["winner_count"].map(lambda v: f"{int(v):,}")
        show["1인 당첨금"] = show["win_amount"].map(lambda v: f"{int(v):,}원")
        st.dataframe(show[["등수", "당첨자 수", "1인 당첨금"]], hide_index=True, use_container_width=True)
        st.caption("금액은 동행복권 표기 기준 1인 당첨금입니다.")

    st.subheader("번호로 회차 찾기")
    picked = st.multiselect("본번호에 포함된 번호 (모두 포함)", options=list(range(1, 46)))
    hits = search_by_numbers(draws, [int(n) for n in picked])
    st.caption(f"{len(hits):,}회차")
    if not hits.empty:
        view = hits[["draw_no", "draw_date", *NUMBER_COLS, "bonus"]].sort_values("draw_no", ascending=False)
        view = view.rename(
            columns={
                "draw_no": "회차",
                "draw_date": "추첨일",
                "bonus": "보너스",
                **{f"n{i}": f"번호{i}" for i in range(1, 7)},
            }
        )
        st.dataframe(view.head(100), hide_index=True, use_container_width=True)
    footer()


def page_frequency() -> None:
    st.title("번호 출현 빈도")
    if not require_db():
        footer()
        return
    tables = get_tables()
    if tables is None:
        return
    draws, _ = tables
    period = render_sidebar(draws)
    scoped = scoped_draws(draws, period)
    include_bonus = st.checkbox("보너스 번호 포함", value=False)
    freq = number_frequency(scoped, include_bonus=include_bonus)
    st.altair_chart(
        bar_chart(freq, "number:O", "count:Q", "번호별 출현 횟수", "번호", "횟수"),
        use_container_width=True,
    )
    grid = freq.copy()
    grid["행"] = (grid["number"] - 1) // 9
    grid["열"] = (grid["number"] - 1) % 9
    heat = (
        alt.Chart(grid)
        .mark_rect()
        .encode(
            x=alt.X("열:O", axis=None),
            y=alt.Y("행:O", axis=None),
            color=alt.Color("count:Q", title="횟수", scale=alt.Scale(scheme="blues")),
            tooltip=["number", "count", "ratio"],
        )
    )
    text = (
        alt.Chart(grid)
        .mark_text()
        .encode(
            x="열:O",
            y="행:O",
            text="number:Q",
            color=alt.condition(
                alt.datum.count > float(grid["count"].median()),
                alt.value("white"),
                alt.value("#222"),
            ),
        )
    )
    st.altair_chart((heat + text).properties(title="번호 히트맵 (1~45)", height=280), use_container_width=True)
    show = freq.sort_values("count", ascending=False).copy()
    show["비율"] = (show["ratio"] * 100).map(lambda v: f"{v:.2f}%")
    st.dataframe(
        show.rename(columns={"number": "번호", "count": "횟수"})[["번호", "횟수", "비율"]],
        hide_index=True,
        use_container_width=True,
        height=240,
    )
    footer()


def page_hot_cold() -> None:
    st.title("핫 / 콜드 번호")
    if not require_db():
        footer()
        return
    tables = get_tables()
    if tables is None:
        return
    draws, _ = tables
    period = render_sidebar(draws)
    scoped = scoped_draws(draws, period)
    st.caption("사이드바에서 '최근 N회'를 고르면 최근 구간 핫/콜드를 볼 수 있습니다.")
    top_k = st.slider("상위·하위 개수", min_value=3, max_value=15, value=5)
    include_bonus = st.checkbox("보너스 포함", value=False)
    hot, cold = hot_cold(scoped, top_k=top_k, include_bonus=include_bonus)
    left, right = st.columns(2)
    with left:
        st.subheader("핫 번호")
        st.altair_chart(
            bar_chart(hot, "number:O", "count:Q", "많이 나온 번호", "번호", "횟수"),
            use_container_width=True,
        )
        st.dataframe(hot.rename(columns={"number": "번호", "count": "횟수", "ratio": "비율"}), hide_index=True)
    with right:
        st.subheader("콜드 번호")
        st.altair_chart(
            bar_chart(cold, "number:O", "count:Q", "적게 나온 번호", "번호", "횟수"),
            use_container_width=True,
        )
        st.dataframe(cold.rename(columns={"number": "번호", "count": "횟수", "ratio": "비율"}), hide_index=True)
    footer()


def page_distribution() -> None:
    st.title("홀짝 · 합계 · 연속번호")
    if not require_db():
        footer()
        return
    tables = get_tables()
    if tables is None:
        return
    draws, _ = tables
    period = render_sidebar(draws)
    scoped = scoped_draws(draws, period)
    odd_draws, pattern, sum_dist = odd_even_and_sum(scoped)
    cons_draws, cons_pairs = consecutive_stats(scoped)
    pattern = pattern.copy()
    pattern["패턴"] = pattern["odd_count"].astype(str) + "홀 " + pattern["even_count"].astype(str) + "짝"
    st.altair_chart(
        bar_chart(pattern, "패턴:N", "draw_count:Q", "홀짝 패턴 분포", "홀짝", "회차 수"),
        use_container_width=True,
    )
    if not odd_draws.empty:
        st.altair_chart(
            bar_chart(sum_dist, "number_sum:Q", "draw_count:Q", "번호 합계 분포", "6개 합계", "회차 수"),
            use_container_width=True,
        )
        s = odd_draws["number_sum"]
        c1, c2, c3 = st.columns(3)
        c1.metric("합계 최소", int(s.min()))
        c2.metric("합계 평균", f"{s.mean():.1f}")
        c3.metric("합계 최대", int(s.max()))
    st.subheader("연속번호 (예: 12-13)")
    if cons_pairs.empty:
        st.info("연속번호가 없습니다.")
    else:
        st.altair_chart(
            bar_chart(cons_pairs.head(20), "label:N", "count:Q", "연속번호 쌍 상위 20", "연속쌍", "횟수"),
            use_container_width=True,
        )
        if not cons_draws.empty:
            c = cons_draws["consecutive_pair_count"]
            st.caption(f"연속쌍 0개인 회차 {int((c == 0).sum()):,} · 1개 이상 {int((c >= 1).sum()):,} · 평균 {c.mean():.2f}")
    footer()


def page_pairs() -> None:
    st.title("자주 같이 나온 번호쌍")
    if not require_db():
        footer()
        return
    tables = get_tables()
    if tables is None:
        return
    draws, _ = tables
    period = render_sidebar(draws)
    scoped = scoped_draws(draws, period)
    top_k = st.slider("상위 K개", min_value=10, max_value=40, value=20)
    pairs = number_pairs(scoped, top_k=top_k)
    bonus = bonus_frequency(scoped)
    st.altair_chart(
        bar_chart(pairs, "label:N", "count:Q", f"동시 출현 번호쌍 Top {top_k}", "번호쌍", "횟수"),
        use_container_width=True,
    )
    st.dataframe(
        pairs.rename(columns={"a": "번호A", "b": "번호B", "label": "쌍", "count": "횟수"}),
        hide_index=True,
        use_container_width=True,
    )
    st.subheader("보너스 번호 빈도")
    st.altair_chart(
        bar_chart(bonus, "number:O", "count:Q", "보너스 출현 횟수", "번호", "횟수"),
        use_container_width=True,
    )
    footer()


def page_prizes() -> None:
    st.title("등수별 당첨금 · 당첨자 수 추이")
    if not require_db():
        footer()
        return
    tables = get_tables()
    if tables is None:
        return
    draws, prizes = tables
    period = render_sidebar(draws)
    scoped = scoped_draws(draws, period)
    rank = st.selectbox("등수", options=[1, 2, 3, 4, 5], format_func=lambda r: f"{r}등")
    metric = st.radio("지표", ["1인 당첨금", "당첨자 수"], horizontal=True)
    trend = prize_trend(prizes, scoped, rank=int(rank))
    if trend.empty:
        st.info("표시할 당첨 정보가 없습니다.")
        footer()
        return
    y = "win_amount" if metric == "1인 당첨금" else "winner_count"
    y_title = "1인 당첨금(원)" if metric == "1인 당첨금" else "당첨자 수"
    st.altair_chart(
        line_chart(trend, "draw_no:Q", f"{y}:Q", f"{rank}등 {metric} 추이", "회차", y_title),
        use_container_width=True,
    )
    show = trend.copy()
    show["1인 당첨금"] = show["win_amount"].map(lambda v: f"{int(v):,}원")
    show["당첨자 수"] = show["winner_count"].map(lambda v: f"{int(v):,}")
    st.dataframe(
        show.rename(columns={"draw_no": "회차", "draw_date": "추첨일"})[
            ["회차", "추첨일", "당첨자 수", "1인 당첨금"]
        ].sort_values("회차", ascending=False).head(30),
        hide_index=True,
        use_container_width=True,
    )
    st.caption("1인 당첨금은 동행복권 공개값입니다. 세전/세후 구분은 원문 표기를 따릅니다.")
    footer()
