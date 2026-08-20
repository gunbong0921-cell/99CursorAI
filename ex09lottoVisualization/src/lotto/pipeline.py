from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import DEFAULT_DB_PATH
from .db import (
    connect,
    draw_range,
    existing_draw_nos,
    failed_draw_nos,
    finish_log,
    record_failure,
    save_draw,
    start_log,
    utc_now,
)
from .source import DhlotteryClient, DrawNotFoundError, SourceBlockedError
from .validate import DrawValidationError

LOGGER = logging.getLogger("lotto.collect")


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def _parse_rounds(text: str) -> list[int]:
    rounds: list[int] = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start, end = int(start_s), int(end_s)
            if end < start:
                raise ValueError(f"회차 구간이 올바르지 않습니다: {part}")
            rounds.extend(range(start, end + 1))
        else:
            rounds.append(int(part))
    return sorted(set(rounds))


def collect(
    db_path: Path,
    *,
    delay_sec: float = 0.4,
    retry_failed: bool = False,
    rounds: list[int] | None = None,
    force: bool = False,
) -> int:
    conn = connect(db_path)
    started = utc_now()
    log_id = start_log(conn, started)
    client = DhlotteryClient(delay_sec=delay_sec)
    fetched = skipped = failed = 0

    try:
        latest = client.fetch_latest_no()
        LOGGER.info("공식 최신 회차: %s", latest)
        existing = existing_draw_nos(conn)

        if rounds is not None:
            targets = rounds
        elif retry_failed:
            targets = failed_draw_nos(conn)
            LOGGER.info("실패 회차 재시도: %s건", len(targets))
        else:
            targets = list(range(1, latest + 1))

        if not force:
            before = len(targets)
            targets = [n for n in targets if n not in existing]
            skipped += before - len(targets)

        LOGGER.info("수집 대상 %s회, 이미 저장됨 %s회", len(targets), skipped)

        if not existing and rounds is None and not retry_failed and targets:
            LOGGER.info("DB가 비어 있어 전체 회차를 한 번에 요청합니다 (srchLtEpsd=all)")
            try:
                records = client.fetch_lt645(all_rounds=True)
                wanted = set(targets)
                for record in records:
                    if record.draw_no not in wanted and not force:
                        continue
                    save_draw(conn, record, utc_now())
                    fetched += 1
                    if record.draw_no in wanted:
                        wanted.discard(record.draw_no)
                conn.commit()
                targets = sorted(wanted)
                if targets:
                    LOGGER.warning("전체 응답에 없는 회차 %s건 → 개별 조회", len(targets))
            except (SourceBlockedError, DrawNotFoundError, DrawValidationError) as exc:
                LOGGER.warning("전체 조회 실패, 회차별 수집으로 전환: %s", exc)

        for draw_no in targets:
            if not force and draw_no in existing_draw_nos(conn):
                skipped += 1
                continue
            try:
                record = client.fetch_one(draw_no)
                save_draw(conn, record, utc_now())
                conn.commit()
                fetched += 1
                LOGGER.info("저장 %s회 (%s) %s + 보너스 %s", draw_no, record.draw_date, record.numbers, record.bonus)
            except Exception as exc:  # noqa: BLE001 - 실패 회차는 기록 후 계속
                failed += 1
                record_failure(conn, draw_no, str(exc))
                conn.commit()
                LOGGER.error("실패 %s회: %s", draw_no, exc)

        mn, mx, cnt = draw_range(conn)
        message = f"완료 stored={cnt} range={mn}-{mx} fetched={fetched} skipped={skipped} failed={failed}"
        finish_log(conn, log_id, fetched=fetched, skipped=skipped, failed=failed, message=message)
        LOGGER.info(message)
        return 1 if failed else 0
    except Exception:
        finish_log(
            conn,
            log_id,
            fetched=fetched,
            skipped=skipped,
            failed=failed,
            message="aborted",
        )
        raise
    finally:
        conn.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="동행복권 로또 6/45 당첨결과를 SQLite에 수집합니다. 기존 회차는 건너뜁니다."
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="SQLite 경로")
    parser.add_argument("--delay", type=float, default=0.4, help="개별 요청 최소 간격(초)")
    parser.add_argument("--retry-failed", action="store_true", help="이전에 실패한 회차만 다시 수집")
    parser.add_argument(
        "--rounds",
        type=str,
        help="특정 회차만 수집 (예: 10,11,20-22)",
    )
    parser.add_argument("--force", action="store_true", help="이미 있는 회차도 다시 받아 덮어씀")
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _configure_logging(args.verbose)
    rounds = _parse_rounds(args.rounds) if args.rounds else None
    return collect(
        args.db,
        delay_sec=args.delay,
        retry_failed=args.retry_failed,
        rounds=rounds,
        force=args.force,
    )


if __name__ == "__main__":
    sys.exit(main())
