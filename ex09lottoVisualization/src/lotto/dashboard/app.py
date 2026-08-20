from __future__ import annotations

import streamlit as st

from lotto.dashboard.pages import (
    page_distribution,
    page_frequency,
    page_hot_cold,
    page_intro,
    page_lookup,
    page_pairs,
    page_prizes,
)


def run() -> None:
    st.set_page_config(page_title="로또 6/45 시각화", layout="wide")
    pages = {
        "개요": [
            st.Page(page_intro, title="소개", url_path="intro"),
        ],
        "조회": [
            st.Page(page_lookup, title="회차 조회", url_path="lookup"),
        ],
        "분석": [
            st.Page(page_frequency, title="번호 빈도", url_path="frequency"),
            st.Page(page_hot_cold, title="핫·콜드", url_path="hot-cold"),
            st.Page(page_distribution, title="홀짝·합계·연속", url_path="distribution"),
            st.Page(page_pairs, title="번호쌍·보너스", url_path="pairs"),
            st.Page(page_prizes, title="당첨금 추이", url_path="prizes"),
        ],
    }
    st.navigation(pages).run()
