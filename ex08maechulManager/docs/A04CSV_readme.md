# CSV 매출 이관 작업 내용

선택한 CSV 폴더의 파일을 `매출.xlsx`의 매출 시트에 넣고, 처리가 끝난 파일은 그 폴더의 `completed`로 옮기는 작업 기록입니다.

## 목적

- 실행 시 tkinter 대화 상자로 CSV 원본 폴더와 `매출.xlsx`를 고른다. 기본 경로는 `C:\`이다.
- 선택한 폴더의 CSV를 읽어 선택한 엑셀의 `매출` 시트에 출력한다.
- 읽기가 끝난 파일은 선택한 폴더의 `completed`로 이동한다.
- 구현은 Python과 프로젝트 `.venv`를 사용한다.

## 확정된 동작

요구사항을 확인한 뒤 아래처럼 정했습니다.

1. 실행하면 CSV 원본 폴더와 `매출.xlsx`를 대화 상자로 고른다. 기본 경로는 `C:\`이다. 취소하면 종료한다.
2. 선택한 csv 폴더(`completed` 제외)의 모든 CSV를 파일명 가나다순으로 읽는다.
3. 선택한 `매출.xlsx`의 `매출` 시트를 비우고, CSV 헤더 그대로 전체 교체한다.
4. 다른 시트는 그대로 둔다.
5. `매출.xlsx`와 `매출` 시트가 없으면 오류로 중단한다. (엑셀 변경 없음, 파일 이동 없음)
6. 정상 처리된 CSV만 선택한 폴더의 `completed`로 옮긴다. 폴더가 없으면 만들고, 같은 이름은 덮어쓴다.
7. 실패한 CSV는 선택한 csv 폴더에 남긴다.
8. CSV가 하나도 없으면 엑셀을 변경하지 않고 종료한다.
9. CSV 인코딩은 UTF-8을 먼저 시도하고, 실패하면 CP949로 재시도한다.
10. 숫자 컬럼(`매출수량`, `매출금액`, `매출이익`, `단가`)은 숫자로 기록한다.

CSV 헤더(그대로 사용):

`매출일, 영업소, 영업담당, 기간, 전표번호, 상품코드, 상품명, 대분류, 중분류, 소분류, 거래처코드, 거래처명, 매출수량, 매출금액, 매출이익, 단가`

## 산출물

### 문서 (`docs`)

| 파일 | 내용 |
| --- | --- |
| [A01CSV.md](A01CSV.md) | 사양서. 경로, 컬럼, 처리 규칙, 작업 체크리스트 |
| [A02CSV_flow.md](A02CSV_flow.md) | 머메이드 플로차트 |
| [A03CSV_sequence.md](A03CSV_sequence.md) | 머메이드 시퀀스 차트 |
| [A04CSV_readme.md](A04CSV_readme.md) | 이 작업 내용 정리 |

### 프로그램 (프로젝트 루트)

| 파일 | 내용 |
| --- | --- |
| [PA_CSV_to_Excel.py](../PA_CSV_to_Excel.py) | A01CSV 사양에 맞춘 실행 프로그램 |
| [import_sales.py](../import_sales.py) | 동일 이관을 먼저 구현·실행한 스크립트 |
| [requirements.txt](../requirements.txt) | `pandas==3.0.5`, `openpyxl==3.1.5` |

Python은 프로젝트 루트 `.venv`에서 실행합니다. 만든 `.py` 파일은 삭제하지 않습니다.

## 작업 경과

1. 사양 확정 후 [A01CSV.md](A01CSV.md)에 저장했다.
2. 플로차트와 시퀀스 차트를 [A02CSV_flow.md](A02CSV_flow.md), [A03CSV_sequence.md](A03CSV_sequence.md)에 저장했다.
3. `.venv`를 만들고 pandas, openpyxl을 설치했다.
4. `import_sales.py`로 1차 이관을 실행했다. CSV 36개, 데이터 2,442행, 성공 파일을 `completed`로 이동했다.
5. 사양 기준으로 [PA_CSV_to_Excel.py](../PA_CSV_to_Excel.py)를 프로젝트 루트에 작성했다. 당시 `csv` 폴더는 비어 있어 엑셀을 변경하지 않고 종료했다.
6. `completed`의 CSV 36개를 다시 `resData/csv`로 옮겼다.
7. `PA_CSV_to_Excel.py`를 실행했다. `매출.xlsx`를 열 때 openpyxl이 잘못된 스타일 인덱스를 만나 `IndexError`로 실패했다. 엑셀은 바꾸지 않았고, 파일도 이동하지 않았다.
8. 셀/행/열 스타일 인덱스가 범위를 벗어나면 기본 스타일로 건너뛰도록 프로그램을 수정했다.
9. 다시 실행해 CSV 36개를 모두 이관하고 `completed`로 이동했다.
10. `PA_CSV_to_Excel.py` 시작 부분에 tkinter.filedialog를 넣었다. CSV 원본 폴더와 `매출.xlsx`를 고른 뒤, 기존 집계·completed 이동을 그대로 수행한다. 대화 상자 기본 경로는 `C:\`이다.

## 실행 방법

```powershell
.\.venv\Scripts\python.exe .\PA_CSV_to_Excel.py
```

실행하면 먼저 CSV 원본 폴더를 고르고, 이어서 `매출.xlsx`를 고릅니다. 기본 경로는 `C:\`입니다.

가상 환경이 없거나 패키지가 없으면:

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python.exe .\PA_CSV_to_Excel.py
```

처리할 CSV는 선택한 폴더 바로 아래에 둡니다. `completed` 안의 파일은 읽지 않습니다.

다시 이관하려면 `completed`의 파일을 CSV 원본 폴더로 옮긴 뒤 같은 명령을 실행하면 됩니다.

## 실행 결과

### 1차: `import_sales.py`

- 수집 CSV: 36개 (광주/대구/대전/부산/서울/인천 × 2025-07 ~ 2025-12)
- 성공: 36개, 실패: 0개
- 매출 시트 기록: 헤더 1행 + 데이터 2,442행
- 다른 시트 유지
- 성공 파일을 `resData/csv/completed`로 이동

### 2차: `PA_CSV_to_Excel.py` (스타일 오류)

- CSV 36개는 읽기 성공
- `매출.xlsx` 저장 단계에서 `IndexError: list index out of range`
- 엑셀 미변경, 파일 이동 없음

원인: 엑셀 파일의 셀/열/행 스타일 번호가 openpyxl이 가진 스타일 목록 범위를 벗어남.

조치: `WorksheetReader`의 셀·서식·열·행 바인딩에서 잘못된 스타일 인덱스는 건너뛰거나 기본 스타일을 쓰도록 수정.

### 3차: `PA_CSV_to_Excel.py` (성공)

- 수집 CSV: 36개
- 성공: 36개, 실패: 0개
- 기록 행 수: 2,442
- 엑셀: `resData/매출.xlsx`의 `매출` 시트
- 이동 경로: `resData/csv/completed`

현재 `csv` 폴더 바로 아래에는 처리할 CSV가 없고, 36개 파일은 `completed`에 있습니다.

## 처리 흐름 요약

1. 대화 상자로 CSV 원본 폴더와 `매출.xlsx`를 고른다. 기본 경로는 `C:\`이다.
2. 선택한 폴더에서 `.csv`만 수집하고 파일명순으로 정렬한다.
3. 선택한 엑셀과 `매출` 시트 존재를 확인한다.
4. 각 CSV를 UTF-8(필요 시 CP949)로 읽고 헤더를 검증한다.
5. 성공한 행만 합친 뒤 `매출` 시트를 비우고 다시 쓴다. 다른 시트는 유지한다.
6. 엑셀 저장에 성공하면 해당 CSV만 `completed`로 이동한다.
7. 처리 건수, 성공/실패 파일명, 출력 경로를 콘솔에 출력한다.

상세 분기는 [A02CSV_flow.md](A02CSV_flow.md), 호출 순서는 [A03CSV_sequence.md](A03CSV_sequence.md)를 참고합니다.

## 프로젝트 구조

```text
ex08maechulManager/
  PA_CSV_to_Excel.py
  import_sales.py
  requirements.txt
  .venv/
  docs/
    A01CSV.md
    A02CSV_flow.md
    A03CSV_sequence.md
    A04CSV_readme.md
  resData/
    매출.xlsx
    청구서.xlsx
    csv/
      completed/
        광주_2025-07.csv ... 인천_2025-12.csv
```
