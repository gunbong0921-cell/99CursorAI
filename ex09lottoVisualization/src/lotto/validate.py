from __future__ import annotations

from .models import DrawRecord


class DrawValidationError(ValueError):
    """회차 데이터가 품질 규칙을 만족하지 않을 때."""


def validate_draw(record: DrawRecord) -> None:
    if record.draw_no < 1:
        raise DrawValidationError(f"회차 번호가 1 미만입니다: {record.draw_no}")

    numbers = list(record.numbers)
    if len(numbers) != 6:
        raise DrawValidationError(f"{record.draw_no}회: 본번호가 6개가 아닙니다")
    if any(n < 1 or n > 45 for n in numbers):
        raise DrawValidationError(f"{record.draw_no}회: 본번호 범위 오류 {numbers}")
    if len(set(numbers)) != 6:
        raise DrawValidationError(f"{record.draw_no}회: 본번호 중복 {numbers}")
    if record.bonus < 1 or record.bonus > 45:
        raise DrawValidationError(f"{record.draw_no}회: 보너스 범위 오류 {record.bonus}")
    if record.bonus in numbers:
        raise DrawValidationError(f"{record.draw_no}회: 보너스가 본번호와 중복")

    ranks = [p.rank for p in record.prizes]
    if sorted(ranks) != [1, 2, 3, 4, 5]:
        raise DrawValidationError(f"{record.draw_no}회: 등수 구성 오류 {ranks}")
    for prize in record.prizes:
        if prize.winner_count < 0 or prize.win_amount < 0:
            raise DrawValidationError(f"{record.draw_no}회: 당첨 수치 음수")
