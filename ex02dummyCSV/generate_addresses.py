#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
경기도 공공배달앱 가맹점 CSV용 가상 주소 생성 스크립트

시군명 필드를 기준으로 해당 시/군 행정구역 범위 내에서
그럴싸한 도로명주소, 지번주소, 우편번호, WGS84 좌표를 생성합니다.

사용법:
    python generate_addresses.py [입력CSV] [출력CSV]

    인자를 생략하면 기본 파일명(경기도공공배달앱배달특급가맹점.csv)을 사용합니다.
    출력 파일을 생략하면 입력 파일을 덮어씁니다.
"""

from __future__ import annotations

import csv
import random
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CityProfile:
    """시/군별 가상 주소 생성에 사용할 프로필."""

    canonical: str
    districts: tuple[str, ...]  # 구/군 내부 구. 없으면 빈 튜플
    dongs: tuple[str, ...]
    roads: tuple[str, ...]
    postal_codes: tuple[str, ...]  # 5자리 우편번호 후보
    lat_range: tuple[float, float]
    lng_range: tuple[float, float]
    has_eup_myeon: bool = False  # 군 지역 여부


# 시군명 별칭 → 표준 키 매핑 (데이터 오타/표기 차이 정규화)
CITY_ALIASES: dict[str, str] = {
    "남양주시": "남양주",
    "의정부시": "의정부",
    "동두천시": "동두천",
    "성남시분": "성남시",
    "성동구": "성남시",  # 오기입 추정 → 성남시 범위 사용
}


def _p(prefix: str, start: int, end: int) -> tuple[str, ...]:
    """우편번호 prefix + 번호 범위로 5자리 코드 목록 생성."""
    return tuple(f"{prefix}{i:02d}" for i in range(start, end + 1))


CITY_PROFILES: dict[str, CityProfile] = {
    "수원시": CityProfile(
        "수원시",
        ("장안구", "권선구", "팔달구", "영통구"),
        ("영통동", "매탄동", "원천동", "광교동", "하동", "연무동", "정자동", "율전동", "권선동", "세류동"),
        ("광교중앙로", "정자로", "수원천로", "경수대로", "동수원로", "효원로", "매탄로", "영통로"),
        _p("16", 2, 39) + _p("16", 40, 99),
        (37.240, 37.345),
        (126.945, 127.085),
    ),
    "성남시": CityProfile(
        "성남시",
        ("수정구", "중원구", "분당구"),
        ("분당동", "정자동", "서현동", "수내동", "야탑동", "금곡동", "신흥동", "태평동", "양지동"),
        ("분당로", "불정로", "판교역로", "성남대로", "수진로", "황새울로", "정자일로", "탄천상로"),
        _p("13", 1, 24) + _p("13", 4, 9) + _p("13", 50, 59),
        (37.380, 37.470),
        (127.050, 127.165),
    ),
    "고양시": CityProfile(
        "고양시",
        ("덕양구", "일산동구", "일산서구"),
        ("주교동", "행신동", "화정동", "마두동", "백석동", "정발산동", "장항동", "대화동"),
        ("고양대로", "화중로", "백석로", "정발산로", "중앙로", "원당로", "일산로", "강선로"),
        _p("10", 1, 29) + _p("10", 30, 49) + _p("10", 50, 69),
        (37.580, 37.700),
        (126.780, 126.920),
    ),
    "용인시": CityProfile(
        "용인시",
        ("처인구", "기흥구", "수지구"),
        ("김량장동", "역북동", "구갈동", "보정동", "동백동", "상현동", "풍덕천동", "신갈동"),
        ("용구대로", "중부대로", "포곡로", "동백로", "수지로", "기흥로", "용인로", "평촌로"),
        _p("16", 80, 99) + _p("17", 0, 19) + _p("17", 20, 39),
        (37.180, 37.320),
        (127.050, 127.280),
    ),
    "부천시": CityProfile(
        "부천시",
        ("원미구", "소사구", "오정구"),
        ("중동", "상동", "심곡동", "역곡동", "송내동", "춘의동", "오정동", "원종동"),
        ("길주로", "부천로", "신흥로", "중동로", "소사로", "원미로", "성곡로", "삼작로"),
        _p("14", 4, 19) + _p("14", 20, 39) + _p("14", 60, 79),
        (37.460, 37.530),
        (126.740, 126.820),
    ),
    "안산시": CityProfile(
        "안산시",
        ("상록구", "단원구"),
        ("본오동", "사동", "월피동", "성포동", "고잔동", "와동", "선부동", "중앙동"),
        ("중앙대로", "고잔로", "선부로", "해안로", "원포로", "충장로", "부곡로", "안산로"),
        _p("15", 2, 19) + _p("15", 20, 39) + _p("15", 40, 59),
        (37.280, 37.360),
        (126.780, 126.880),
    ),
    "안양시": CityProfile(
        "안양시",
        ("만안구", "동안구"),
        ("안양동", "비산동", "평촌동", "호계동", "관양동", "부림동", "갈산동", "석수동"),
        ("안양로", "평촌대로", "시민로", "경수대로", "동안로", "만안로", "부림로", "학의로"),
        _p("14", 0, 19) + _p("14", 20, 39),
        (37.360, 37.420),
        (126.920, 127.000),
    ),
    "남양주": CityProfile(
        "남양주",
        (),
        ("와부읍", "조안면", "오남읍", "별내동", "다산동", "금곡동", "화도읍", "수동면"),
        ("경춘로", "다산로", "별내로", "화도로", "와부로", "오남로", "진접로", "양정로"),
        _p("12", 0, 29) + _p("12", 30, 49),
        (37.520, 37.720),
        (127.120, 127.320),
    ),
    "화성시": CityProfile(
        "화성시",
        (),
        ("동탄동", "병점동", "향남읍", "봉담읍", "우정읍", "팔탄면", "매송면", "기배동"),
        ("동탄대로", "병점로", "향남로", "봉담로", "화성로", "수원로", "정남면로", "서해로"),
        _p("18", 2, 29) + _p("18", 30, 59) + _p("18", 60, 79),
        (37.050, 37.250),
        (126.750, 127.150),
    ),
    "평택시": CityProfile(
        "평택시",
        (),
        ("평택동", "서정동", "통복동", "비전동", "용이동", "청북읍", "고덕동", "신장동"),
        ("평택로", "비전로", "송탄로", "청북로", "고덕로", "신장로", "서정로", "팽성로"),
        _p("17", 80, 99) + _p("17", 60, 79),
        (36.950, 37.080),
        (126.950, 127.150),
    ),
    "의정부": CityProfile(
        "의정부",
        (),
        ("의정부동", "호원동", "장암동", "신곡동", "가능동", "금오동", "민락동", "용현동"),
        ("의정부로", "호국로", "민락로", "장곡로", "가능로", "신곡로", "탑석로", "경민로"),
        _p("11", 6, 29) + _p("11", 30, 49),
        (37.700, 37.780),
        (127.010, 127.110),
    ),
    "시흥시": CityProfile(
        "시흥시",
        (),
        ("대야동", "정왕동", "은행동", "신천동", "월곶동", "군자동", "배곧동", "거모동"),
        ("시흥로", "정왕로", "은행로", "대야로", "월곶로", "군자로", "배곧로", "거모로"),
        _p("14", 9, 29) + _p("14", 30, 49),
        (37.320, 37.420),
        (126.720, 126.850),
    ),
    "파주시": CityProfile(
        "파주시",
        (),
        ("금촌동", "운정동", "문산읍", "교하동", "탄현면", "법원읍", "조리읍", "월롱면"),
        ("경의로", "운정로", "금촌로", "문산로", "교하로", "탄현로", "법원로", "헤이리로"),
        _p("10", 8, 29) + _p("10", 90, 99),
        (37.700, 37.900),
        (126.680, 126.850),
    ),
    "김포시": CityProfile(
        "김포시",
        (),
        ("김포동", "장기동", "구래동", "운양동", "풍무동", "사우동", "양촌읍", "통진읍"),
        ("김포대로", "장기로", "구래로", "운양로", "풍무로", "사우로", "양촌로", "통진로"),
        _p("10", 0, 29) + _p("10", 30, 49),
        (37.580, 37.680),
        (126.580, 126.720),
    ),
    "광주시": CityProfile(
        "광주시",
        (),
        ("경안동", "송정동", "오포읍", "초월읍", "곤지암읍", "퇴촌면", "남종면", "실촌면"),
        ("경안로", "송정로", "오포로", "초월로", "곤지암로", "광주로", "남한산성로", "도척로"),
        _p("12", 7, 29) + _p("12", 30, 49),
        (37.350, 37.450),
        (127.200, 127.350),
    ),
    "광명시": CityProfile(
        "광명시",
        (),
        ("광명동", "철산동", "하안동", "소하동", "일직동", "옥길동"),
        ("광명로", "철산로", "하안로", "소하로", "일직로", "옥길로", "디지털로", "범안로"),
        _p("14", 2, 19) + _p("14", 20, 29),
        (37.450, 37.490),
        (126.840, 126.890),
    ),
    "군포시": CityProfile(
        "군포시",
        (),
        ("군포동", "산본동", "금정동", "당동", "대야동", "송부동"),
        ("군포로", "산본로", "금정로", "당동로", "대야로", "송부로", "번영로", "청계로"),
        _p("15", 8, 19) + _p("15", 20, 29),
        (37.320, 37.370),
        (126.920, 126.970),
    ),
    "하남시": CityProfile(
        "하남시",
        (),
        ("신장동", "덕풍동", "풍산동", "망월동", "천현동", "감일동", "춘궁동", "감북동"),
        ("하남대로", "덕풍로", "풍산로", "미사대로", "감일로", "천현로", "신장로", "망월로"),
        _p("12", 9, 29) + _p("12", 30, 39),
        (37.520, 37.570),
        (127.180, 127.240),
    ),
    "오산시": CityProfile(
        "오산시",
        (),
        ("오산동", "원동", "궐동", "세마동", "초평동", "가수동", "내삼미동", "지곶동"),
        ("오산로", "원동로", "궐동로", "세마로", "가수로", "내삼미로", "지곶로", "성호로"),
        _p("18", 1, 19) + _p("18", 20, 29),
        (37.130, 37.180),
        (127.040, 127.100),
    ),
    "이천시": CityProfile(
        "이천시",
        (),
        ("중리동", "관고동", "증포동", "부발읍", "신둔면", "마장면", "모가면", "설성면"),
        ("이천로", "증포로", "부발로", "신둔로", "마장로", "모가로", "설성로", "중리로"),
        _p("17", 3, 29) + _p("17", 30, 39),
        (37.240, 37.320),
        (127.400, 127.520),
    ),
    "안성시": CityProfile(
        "안성시",
        (),
        ("안성동", "공도읍", "죽산면", "보개면", "금광면", "서운면", "미양면", "대덕면"),
        ("안성로", "공도로", "죽산로", "보개로", "금광로", "서운로", "미양로", "대덕로"),
        _p("17", 5, 29) + _p("17", 30, 39),
        (37.000, 37.100),
        (127.250, 127.350),
    ),
    "양주시": CityProfile(
        "양주시",
        (),
        ("양주동", "회천동", "옥정동", "덕계동", "광적면", "남면", "은현면", "장흥면"),
        ("양주로", "회천로", "옥정로", "덕계로", "광적로", "남면로", "은현로", "장흥로"),
        _p("11", 4, 29) + _p("11", 50, 59),
        (37.780, 37.880),
        (126.980, 127.080),
    ),
    "구리시": CityProfile(
        "구리시",
        (),
        ("교문동", "수택동", "인창동", "토평동", "갈매동", "아천동", "동구동"),
        ("구리로", "수택로", "인창로", "토평로", "갈매로", "아천로", "교문로", "경춘로"),
        _p("11", 9, 19) + _p("11", 20, 29),
        (37.580, 37.620),
        (127.120, 127.160),
    ),
    "포천시": CityProfile(
        "포천시",
        (),
        ("포천동", "소흘읍", "군내면", "내촌면", "가산면", "신북면", "창수면", "영중면"),
        ("포천로", "소흘로", "군내로", "내촌로", "가산로", "신북로", "창수로", "영중로"),
        _p("11", 1, 19) + _p("11", 20, 29),
        (37.800, 37.950),
        (127.150, 127.300),
    ),
    "동두천": CityProfile(
        "동두천",
        (),
        ("생연동", "지행동", "보산동", "송내동", "상패동", "안흥동", "탑동동"),
        ("동두천로", "지행로", "보산로", "송내로", "상패로", "안흥로", "탑동로", "평화로"),
        _p("11", 3, 19) + _p("11", 20, 29),
        (37.880, 37.930),
        (127.040, 127.090),
    ),
    "과천시": CityProfile(
        "과천시",
        (),
        ("중앙동", "갈현동", "별양동", "부림동", "과천동", "문원동"),
        ("과천대로", "갈현로", "별양로", "부림로", "중앙로", "문원로", "막계로", "관문로"),
        _p("13", 8, 19),
        (37.410, 37.440),
        (126.980, 127.010),
    ),
    "의왕시": CityProfile(
        "의왕시",
        (),
        ("의왕동", "고천동", "내손동", "오전동", "청계동", "포일동", "학의동"),
        ("의왕로", "고천로", "내손로", "오전로", "청계로", "포일로", "학의로", "부곡로"),
        _p("16", 0, 19) + _p("16", 20, 29),
        (37.320, 37.360),
        (126.960, 127.010),
    ),
    "여주시": CityProfile(
        "여주시",
        (),
        ("여주동", "점동면", "흥천면", "금사면", "능서면", "대신면", "북내면", "강천면"),
        ("여주로", "점동로", "흥천로", "금사로", "능서로", "대신로", "북내로", "강천로"),
        _p("12", 6, 19) + _p("12", 20, 29),
        (37.250, 37.350),
        (127.550, 127.680),
    ),
    "양평군": CityProfile(
        "양평군",
        (),
        ("양평읍", "강상면", "강하면", "옥천면", "서종면", "단월면", "청운면", "양서면"),
        ("양평로", "강상로", "강하로", "옥천로", "서종로", "단월로", "청운로", "양서로"),
        _p("12", 5, 19) + _p("12", 20, 29),
        (37.400, 37.550),
        (127.400, 127.600),
        has_eup_myeon=True,
    ),
    "가평군": CityProfile(
        "가평군",
        (),
        ("가평읍", "설악면", "청평면", "상면", "하면", "북면", "조종면"),
        ("가평로", "설악로", "청평로", "상면로", "하면로", "북면로", "조종로", "경춘로"),
        _p("12", 4, 19) + _p("12", 20, 29),
        (37.750, 37.900),
        (127.400, 127.600),
        has_eup_myeon=True,
    ),
    "연천군": CityProfile(
        "연천군",
        (),
        ("연천읍", "전곡읍", "군남면", "청산면", "백학면", "미산면", "왕징면", "신서면"),
        ("연천로", "전곡로", "군남로", "청산로", "백학로", "미산로", "왕징로", "신서로"),
        _p("10", 9, 19) + _p("10", 20, 29),
        (38.000, 38.150),
        (126.950, 127.150),
        has_eup_myeon=True,
    ),
}


FIELDNAMES = [
    "시군명",
    "매장명",
    "사업자등록번호",
    "정제도로명주소",
    "정제지번주소",
    "업종",
    "정제우편번호",
    "정제WGS84위도",
    "정제WGS84경도",
]


def normalize_city(raw: str) -> str:
    """시군명을 표준 키로 정규화."""
    name = (raw or "").strip()
    return CITY_ALIASES.get(name, name)


def resolve_profile(city_name: str) -> CityProfile:
    """시군명에 해당하는 프로필 반환. 없으면 KeyError."""
    key = normalize_city(city_name)
    if key not in CITY_PROFILES:
        raise KeyError(f"등록되지 않은 시군명: {city_name!r} (정규화: {key!r})")
    return CITY_PROFILES[key]


def _pick_district(profile: CityProfile, rng: random.Random) -> str | None:
    return rng.choice(profile.districts) if profile.districts else None


def _pick_dong(profile: CityProfile, rng: random.Random) -> str:
    return rng.choice(profile.dongs)


def _pick_road(profile: CityProfile, rng: random.Random) -> str:
    return rng.choice(profile.roads)


def _pick_postal(profile: CityProfile, rng: random.Random) -> str:
    return rng.choice(profile.postal_codes)


def _pick_coords(profile: CityProfile, rng: random.Random) -> tuple[str, str]:
    lat = rng.uniform(profile.lat_range[0], profile.lat_range[1])
    lng = rng.uniform(profile.lng_range[0], profile.lng_range[1])
    return f"{lat:.6f}", f"{lng:.6f}"


def _road_number(rng: random.Random) -> str:
    main = rng.randint(1, 999)
    if rng.random() < 0.35:
        sub = rng.randint(1, 30)
        return f"{main}-{sub}"
    return str(main)


def _jibun(rng: random.Random) -> str:
    main = rng.randint(1, 1500)
    if rng.random() < 0.45:
        sub = rng.randint(1, 50)
        return f"{main}-{sub}"
    return str(main)


def generate_address_fields(city_name: str, rng: random.Random) -> dict[str, str]:
    """한 행에 채울 주소 관련 필드 생성."""
    profile = resolve_profile(city_name)
    district = _pick_district(profile, rng)
    dong = _pick_dong(profile, rng)
    road = _pick_road(profile, rng)
    road_no = _road_number(rng)
    jibun = _jibun(rng)
    postal = _pick_postal(profile, rng)
    lat, lng = _pick_coords(profile, rng)

    display_city = profile.canonical

    if district:
        road_addr = f"경기도 {display_city} {district} {road} {road_no}"
        lot_addr = f"경기도 {display_city} {district} {dong} {jibun}"
    else:
        road_addr = f"경기도 {display_city} {dong} {road} {road_no}"
        lot_addr = f"경기도 {display_city} {dong} {jibun}"

    return {
        "정제도로명주소": road_addr,
        "정제지번주소": lot_addr,
        "정제우편번호": postal,
        "정제WGS84위도": lat,
        "정제WGS84경도": lng,
    }


def process_csv(
    input_path: Path,
    output_path: Path,
    *,
    seed: int = 42,
    overwrite_existing: bool = False,
) -> dict[str, int]:
    """CSV 파일을 읽어 주소 필드를 채우고 저장."""
    rng = random.Random(seed)
    stats = {"total": 0, "filled": 0, "skipped": 0, "errors": 0}
    unknown_cities: set[str] = set()

    with input_path.open("r", encoding="utf-8-sig", newline="") as infile:
        reader = csv.DictReader(infile)
        if reader.fieldnames != FIELDNAMES:
            raise ValueError(
                f"예상 컬럼과 다릅니다.\n기대: {FIELDNAMES}\n실제: {reader.fieldnames}"
            )
        rows: list[dict[str, str]] = []

        for row in reader:
            stats["total"] += 1
            city = row.get("시군명", "")

            needs_fill = overwrite_existing or not (
                row.get("정제도로명주소")
                and row.get("정제지번주소")
                and row.get("정제우편번호")
                and row.get("정제WGS84위도")
                and row.get("정제WGS84경도")
            )

            if not needs_fill:
                stats["skipped"] += 1
                rows.append(row)
                continue

            try:
                generated = generate_address_fields(city, rng)
                row.update(generated)
                stats["filled"] += 1
            except KeyError:
                stats["errors"] += 1
                unknown_cities.add(city)
            rows.append(row)

    with output_path.open("w", encoding="utf-8-sig", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    if unknown_cities:
        print("경고: 등록되지 않은 시군명:", ", ".join(sorted(unknown_cities)))

    return stats


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    default_input = base_dir / "경기도공공배달앱배달특급가맹점.csv"

    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_input
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path

    if not input_path.exists():
        print(f"입력 파일을 찾을 수 없습니다: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"입력: {input_path}")
    print(f"출력: {output_path}")

    stats = process_csv(input_path, output_path)
    print(
        f"완료 - 전체 {stats['total']:,}행, "
        f"채움 {stats['filled']:,}행, "
        f"건너뜀 {stats['skipped']:,}행, "
        f"오류 {stats['errors']:,}행"
    )


if __name__ == "__main__":
    main()
