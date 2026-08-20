# 로또 6/45 당첨번호 수집·분석·시각화

동행복권 로또 6/45 당첨결과를 모아 SQLite에 저장하고, 통계를 계산한 뒤 Streamlit으로 보여 주는 포트폴리오 프로젝트입니다.

통계는 과거 데이터 분석이며 당첨을 보장하지 않습니다. 데이터 출처는 동행복권입니다.

## 준비

Windows에서 프로젝트 루트의 `.venv`만 사용합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

## Part 1. 수집

```powershell
.\.venv\Scripts\python.exe collect.py
```

- 결과는 `data/lotto.db`에 저장됩니다.
- 다시 실행하면 이미 있는 회차는 건너뛰고 신규 회차만 추가합니다.

```powershell
.\.venv\Scripts\python.exe collect.py --retry-failed
.\.venv\Scripts\python.exe collect.py --rounds 1230-1237
```

## Part 2. 분석

```powershell
.\.venv\Scripts\python.exe analyze.py
.\.venv\Scripts\python.exe analyze.py --last 50
.\.venv\Scripts\python.exe analyze.py --start 1000 --end 1237
```

## Part 3. 시각화

```powershell
.\.venv\Scripts\streamlit.exe run streamlit_app.py
```

브라우저에서 소개, 회차 조회, 번호 빈도, 핫/콜드, 홀짝·합계·연속, 번호쌍·보너스, 당첨금 추이 페이지를 확인합니다.

## 출처 · 면책

- 원본: 동행복권 (https://www.dhlottery.co.kr)
- 본 프로젝트는 개인 학습·포트폴리오 목적의 재가공입니다.
- 번호 예측·추천 기능은 없습니다.
