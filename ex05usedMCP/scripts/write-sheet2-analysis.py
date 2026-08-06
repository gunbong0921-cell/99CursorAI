"""Create 시트2 and write stock comparison data."""
from google.oauth2 import service_account
from googleapiclient.discovery import build

SPREADSHEET_ID = "12i35R3M2nS5sksUTj-_eRkrklE1H6Ja9EYs0C_DfE0A"
CREDS_PATH = r"C:\02Workspaces\99CursorAI\symmetric-lore-504707-s0-bc9098aa1ff0.json"
SHEET_TITLE = "시트2"

ROWS = [
    ["삼성전자 vs SK하이닉스 비교 분석", "", "", "", "", ""],
    ["기준일", "2026-08-06", "데이터 출처", "Yahoo Finance (yfinance MCP)", "", ""],
    ["", "", "", "", "", ""],
    ["항목", "삼성전자 (005930)", "SK하이닉스 (000660)", "비고", "", ""],
    ["현재가", "230,500원", "1,495,000원", "", "", ""],
    ["시가총액", "약 1,513조원", "약 1,061조원", "", "", ""],
    ["PER (예상 EPS 기준)", "4.74배", "4.38배", "Forward PER: 3.45 / 3.33", "", ""],
    ["EPS (당해 연도 예상)", "48,621원", "341,636원", "", "", ""],
    ["배당수익률", "0.62%", "0.19%", "", "", ""],
    ["", "", "", "", "", ""],
    ["1년 추세 분석 (최근 1년 일봉 기준)", "", "", "", "", ""],
    ["종목", "1년 수익률", "52주 고가 대비", "200일선 대비", "50일선 대비", "추세 판단"],
    [
        "삼성전자",
        "+239.2%",
        "-38.5% (고점 374,500원)",
        "+17.9% (200일 195,425원)",
        "-22.9% (50일 298,780원)",
        "장기 상승 / 단기 조정(하락)",
    ],
    [
        "SK하이닉스",
        "+481.0%",
        "-49.9% (고점 2,987,000원)",
        "+25.6% (200일 1,190,035원)",
        "-30.9% (50일 2,164,780원)",
        "장기 상승 / 단기 조정(하락)",
    ],
    ["", "", "", "", "", ""],
    ["종합 해설", "", "", "", "", ""],
    [
        "삼성전자",
        "지난 1년간 약 67,947원→230,500원으로 강한 상승 추세였으나, 5~6월 고점(374,500원) 이후 단기 하락 조정 국면입니다. 200일 이동평균선 위에 있어 중기 상승 기조는 유지되나, 50일선 아래로 내려와 단기 모멘텀은 약화된 상태입니다.",
        "",
        "",
        "",
        "",
    ],
    [
        "SK하이닉스",
        "지난 1년간 약 257,424원→1,495,000원으로 메모리 반도체 슈퍼사이클에 힘입어 급격한 상승 추세를 보였습니다. 52주 최고가(2,987,000원) 대비 약 50% 조정 중이나, 1년 전 대비 수익률은 여전히 매우 높습니다. 최근 2~3개월은 고점 대비 하락 조정, 200일선 위·50일선 아래로 단기 약세입니다.",
        "",
        "",
        "",
        "",
    ],
    [
        "비교 요약",
        "두 종목 모두 1년 관점에서는 '상승 추세', 최근 2~3개월은 '고점 대비 하락 조정'으로 해석할 수 있습니다. PER·EPS 면에서 SK하이닉스의 이익 규모가 더 크고, 배당수익률은 삼성전자가 더 높습니다.",
        "",
        "",
        "",
        "",
    ],
]


def main() -> None:
    creds = service_account.Credentials.from_service_account_file(
        CREDS_PATH,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    service = build("sheets", "v4", credentials=creds)
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheet_titles = {s["properties"]["title"] for s in spreadsheet["sheets"]}

    if SHEET_TITLE not in sheet_titles:
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={
                "requests": [
                    {"addSheet": {"properties": {"title": SHEET_TITLE}}}
                ]
            },
        ).execute()

    service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_TITLE}!A:F",
    ).execute()

    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_TITLE}!A1",
        valueInputOption="USER_ENTERED",
        body={"values": ROWS},
    ).execute()

    print(f"Wrote {len(ROWS)} rows to {SHEET_TITLE}")


if __name__ == "__main__":
    main()
