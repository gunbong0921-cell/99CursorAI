from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

from .models import DrawRecord, PrizeRecord
from .validate import DrawValidationError, validate_draw

LOGGER = logging.getLogger("lotto.collect")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "Lotto645PortfolioCollector/1.0 (personal/educational; +local-only)"
)
BASE = "https://www.dhlottery.co.kr"
LT645_URL = f"{BASE}/lt645/selectPstLt645Info.do"
LEGACY_JSON_URL = f"{BASE}/common.do"
BYWIN_URL = f"{BASE}/gameResult.do"

TIMEOUT = 30
RETRY_COUNT = 3
RETRY_BACKOFF = 1.5


class SourceBlockedError(RuntimeError):
    """동행복권이 대기/차단 페이지를 반환할 때."""


class DrawNotFoundError(LookupError):
    """해당 회차 JSON이 없을 때."""


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            "Referer": f"{BASE}/gameResult.do?method=byWin",
        }
    )
    return session


def _raise_if_blocked(response: requests.Response) -> None:
    url = response.url or ""
    if "errorPage" in url:
        raise SourceBlockedError("동행복권이 errorPage로 리다이렉트했습니다. 현재 IP/네트워크에서 접속이 제한된 것으로 보입니다.")
    content_type = (response.headers.get("Content-Type") or "").lower()
    text_head = response.text[:800]
    if "application/json" in content_type:
        return
    if response.text.lstrip().startswith("{") or response.text.lstrip().startswith("["):
        return
    if "서비스 접근 대기" in text_head or "접속이 차단" in text_head:
        raise SourceBlockedError("동행복권이 대기/차단 페이지를 반환했습니다.")


def _get(session: requests.Session, url: str, *, params: dict[str, Any] | None = None) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            response = session.get(url, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            _raise_if_blocked(response)
            return response
        except SourceBlockedError:
            raise
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            LOGGER.warning("요청 실패 (%s/%s) %s: %s", attempt, RETRY_COUNT, url, exc)
            time.sleep(RETRY_BACKOFF * attempt)
    raise RuntimeError(f"요청 재시도 초과: {url}") from last_error


def _parse_ymd(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 8:
        return f"{digits[0:4]}-{digits[4:6]}-{digits[6:8]}"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value or ""):
        return value
    raise DrawValidationError(f"추첨일 형식 오류: {value!r}")


def _int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    if isinstance(value, str):
        value = value.replace(",", "").strip()
    return int(value)


def parse_lt645_item(item: dict[str, Any]) -> DrawRecord:
    numbers = tuple(
        sorted(
            _int(item[f"tm{i}WnNo"])
            for i in range(1, 7)
        )
    )
    prizes = tuple(
        PrizeRecord(
            rank=rank,
            winner_count=_int(item.get(f"rnk{rank}WnNope")),
            win_amount=_int(item.get(f"rnk{rank}WnAmt")),
            sum_win_amount=_int(item.get(f"rnk{rank}SumWnAmt"))
            if item.get(f"rnk{rank}SumWnAmt") is not None
            else None,
        )
        for rank in range(1, 6)
    )
    record = DrawRecord(
        draw_no=_int(item["ltEpsd"]),
        draw_date=_parse_ymd(str(item["ltRflYmd"])),
        numbers=numbers,  # type: ignore[arg-type]
        bonus=_int(item["bnsWnNo"]),
        tot_sell_amount=_int(item["rlvtEpsdSumNtslAmt"])
        if item.get("rlvtEpsdSumNtslAmt") is not None
        else None,
        prizes=prizes,
        source="json",
    )
    validate_draw(record)
    return record


def parse_legacy_json(payload: dict[str, Any], prizes: tuple[PrizeRecord, ...], source: str) -> DrawRecord:
    if payload.get("returnValue") != "success":
        raise DrawNotFoundError(f"legacy JSON 실패: {payload.get('returnValue')}")
    numbers = tuple(sorted(_int(payload[f"drwtNo{i}"]) for i in range(1, 7)))
    record = DrawRecord(
        draw_no=_int(payload["drwNo"]),
        draw_date=_parse_ymd(str(payload["drwNoDate"])),
        numbers=numbers,  # type: ignore[arg-type]
        bonus=_int(payload["bnusNo"]),
        tot_sell_amount=_int(payload["totSellamnt"]) if payload.get("totSellamnt") is not None else None,
        prizes=prizes,
        source=source,
    )
    validate_draw(record)
    return record


def parse_bywin_prizes(html: str) -> tuple[PrizeRecord, ...]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table.tbl_data") or soup.find("table")
    if table is None:
        raise DrawValidationError("회차 HTML에서 당첨 표를 찾지 못했습니다.")

    found: dict[int, PrizeRecord] = {}
    for row in table.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in row.find_all(["th", "td"])]
        if not cells:
            continue
        rank_match = re.search(r"([1-5])\s*등", "".join(cells))
        if not rank_match:
            continue
        rank = int(rank_match.group(1))
        amounts = [int(x.replace(",", "")) for x in re.findall(r"\d[\d,]*", " ".join(cells))]
        # 표 형태: 등수, (게임수), 총당첨금, 당첨게임수, 1게임당 당첨금 ...
        winner_count = 0
        win_amount = 0
        sum_win_amount = None
        if len(amounts) >= 3:
            winner_count = amounts[-2] if amounts[-2] < amounts[-1] or amounts[-1] >= 5000 else amounts[1]
            # 더 안정적으로: 1게임당 당첨금은 보통 마지막 큰 금액 또는 고정 5천/5만
            win_amount = amounts[-1]
            if len(amounts) >= 4:
                sum_win_amount = amounts[-3] if amounts[-3] > win_amount else amounts[1]
        found[rank] = PrizeRecord(
            rank=rank,
            winner_count=winner_count,
            win_amount=win_amount,
            sum_win_amount=sum_win_amount,
        )
    if set(found) != {1, 2, 3, 4, 5}:
        raise DrawValidationError(f"HTML 등수 파싱 실패: {sorted(found)}")
    return tuple(found[i] for i in range(1, 6))


class DhlotteryClient:
    def __init__(self, delay_sec: float = 0.4) -> None:
        self.delay_sec = delay_sec
        self.session = _session()
        self._last_request_at = 0.0

    def _pace(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        wait = self.delay_sec - elapsed
        if wait > 0 and self._last_request_at > 0:
            time.sleep(wait)

    def _request(self, url: str, *, params: dict[str, Any] | None = None) -> requests.Response:
        self._pace()
        response = _get(self.session, url, params=params)
        self._last_request_at = time.monotonic()
        return response

    def fetch_lt645(self, draw_no: int | None = None, *, all_rounds: bool = False) -> list[DrawRecord]:
        params: dict[str, Any] = {"_": int(time.time() * 1000)}
        if all_rounds:
            params["srchLtEpsd"] = "all"
        elif draw_no is not None:
            params["srchLtEpsd"] = draw_no
        response = self._request(LT645_URL, params=params)
        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise SourceBlockedError("lt645 응답이 JSON이 아닙니다.") from exc
        items = ((payload.get("data") or {}).get("list")) or []
        if not items:
            raise DrawNotFoundError(f"lt645 목록이 비었습니다 (draw_no={draw_no})")
        return [parse_lt645_item(item) for item in items]

    def fetch_legacy_json(self, draw_no: int) -> dict[str, Any]:
        response = self._request(
            LEGACY_JSON_URL,
            params={"method": "getLottoNumber", "drwNo": draw_no},
        )
        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise SourceBlockedError("legacy JSON 엔드포인트가 HTML/차단 페이지를 반환했습니다.") from exc
        if payload.get("returnValue") != "success":
            raise DrawNotFoundError(f"{draw_no}회 legacy JSON 없음")
        return payload

    def fetch_bywin_html(self, draw_no: int) -> str:
        response = self._request(BYWIN_URL, params={"method": "byWin", "drwNo": draw_no})
        if "text/html" not in (response.headers.get("Content-Type") or "") and not response.text:
            raise RuntimeError(f"{draw_no}회 HTML이 비었습니다")
        return response.text

    def fetch_latest_no(self) -> int:
        records = self.fetch_lt645()
        return max(r.draw_no for r in records)

    def fetch_one(self, draw_no: int) -> DrawRecord:
        try:
            records = self.fetch_lt645(draw_no)
            for record in records:
                if record.draw_no == draw_no:
                    return record
            raise DrawNotFoundError(f"lt645 응답에 {draw_no}회가 없습니다")
        except (SourceBlockedError, DrawNotFoundError, DrawValidationError, RuntimeError) as primary_exc:
            LOGGER.warning("%s회 lt645 실패, legacy JSON으로 시도: %s", draw_no, primary_exc)

        payload = self.fetch_legacy_json(draw_no)
        try:
            html = self.fetch_bywin_html(draw_no)
            prizes = parse_bywin_prizes(html)
            source = "mixed"
        except Exception as html_exc:  # noqa: BLE001 - 보조 소스 실패 시 1등만으로라도 남기지 않음
            LOGGER.warning("%s회 HTML 등수 파싱 실패: %s", draw_no, html_exc)
            prizes = (
                PrizeRecord(
                    rank=1,
                    winner_count=_int(payload.get("firstPrzwnerCo")),
                    win_amount=_int(payload.get("firstWinamnt")),
                    sum_win_amount=_int(payload.get("firstAccumamnt"))
                    if payload.get("firstAccumamnt") is not None
                    else None,
                ),
            )
            raise DrawValidationError(
                f"{draw_no}회 2~5등 정보를 만들지 못했습니다: {html_exc}"
            ) from html_exc
        return parse_legacy_json(payload, prizes, source)
