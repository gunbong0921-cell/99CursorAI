# 거래처별 청구서 발행 작업 내용

지정한 연월의 매출을 거래처별로 모아 청구서 시트를 만들고, 시트명과 같은 PDF를 저장한 뒤 임시 시트를 지우는 작업 기록입니다.

## 목적

- `매출.xlsx`의 해당 월 매출을 거래처코드별로 추출한다.
- `청구서.xlsx`의 `청구서` 시트를 복사해 거래처별 청구서를 채운다.
- `resData/PDF`에 시트명과 같은 PDF를 저장한다.
- PDF가 끝나면 거래처 시트를 삭제하고 원본 시트만 남긴다.

## 확정된 동작

요구사항을 확인한 뒤 아래처럼 정했습니다.

1. 연월은 실행 시 대화 상자로 고른다. 인자를 주면 대화 상자 없이 `yyyy-mm`을 쓴다.
2. 해당 월 매출이 있는 거래처코드만 청구서를 만든다.
3. 거래처 시트 A열 코드와 매출 K열 코드를 대조한다. 마스터가 없으면 건너뛰고 경고한다.
4. 시트명: `거래처명_YYMM`. 이름이 겹치면 `_2`, `_3`을 붙인다.
5. B5 우편번호, B6 주소, B7 거래처명 (B:G 병합 칸).
6. 품목은 매출일 오름차순으로 20행부터. A 매출일, B 상품명, F 수량, G 단가. 금액 H열은 수식 유지.
7. 16줄을 넘으면 35행과 36행 사이에 행을 넣고 H열 수식과 SUM 범위를 맞춘다.
8. PDF는 `매출.xlsx`와 같은 계층의 `PDF` 폴더에 저장한다. 같은 이름은 덮어쓴다.
9. 끝나면 `청구서`, `청구서 BackUp`, `청구서(sample)`만 남긴다.

## 산출물

### 문서 (`docs`)

| 파일 | 내용 |
| --- | --- |
| [B01Bill.md](B01Bill.md) | 사양서. Excel MCP 조사, 기술 스택, 확정 동작, 구현 체크리스트 |
| [B02Bill_flow.md](B02Bill_flow.md) | 머메이드 플로차트 |
| [B03Bill_sequence.md](B03Bill_sequence.md) | 머메이드 시퀀스 차트 |
| [B04Bill_readme.md](B04Bill_readme.md) | 이 작업 내용 정리 |

### 프로그램 (프로젝트 루트)

| 파일 | 내용 |
| --- | --- |
| [PB_Make_Bill.py](../PB_Make_Bill.py) | B01Bill 사양 실행 프로그램 |
| [requirements.txt](../requirements.txt) | pandas, openpyxl, pywin32 |

Python은 프로젝트 루트 `.venv`에서 실행합니다. 만든 `.py` 파일은 삭제하지 않습니다.

사양서의 실행 파일명은 `PA_Bill.py`였으나, 요청에 따라 실제 파일은 `PB_Make_Bill.py`입니다.

## 기술 스택

- OS: Windows
- 런타임: `.venv` Python 3
- pandas: 매출·거래처 추출, 연월 필터, 거래처코드 대조
- openpyxl: 청구서 시트 복사, 머리글·품목 입력, 행 삽입
- tkinter: 연도·월 선택 대화 상자
- LibreOffice (`soffice.exe`): 시트별 PDF 저장

사양 초안은 Microsoft Excel + pywin32였습니다. Excel COM 대신 LibreOffice 26.2.5.2를 설치하고 PDF 저장에 사용했습니다.

## 작업 경과

1. Excel MCP로 `청구서.xlsx`, `매출.xlsx`의 시트명, 사용 범위, 수식을 조사했다.
2. 중복 거래처명, 대상 거래처, 연월 지정, PDF 방식, 마스터 없음, 품목 순서를 질의로 확정했다.
3. 사양서를 [B01Bill.md](B01Bill.md)에 저장했다.
4. 플로차트와 시퀀스 차트를 [B02Bill_flow.md](B02Bill_flow.md), [B03Bill_sequence.md](B03Bill_sequence.md)에 저장했다.
5. [PB_Make_Bill.py](../PB_Make_Bill.py)를 작성했다. 처음 PDF는 Excel(win32com) 기준이었다.
6. LibreOffice를 설치하고 PDF 저장을 LibreOffice 변환으로 바꿨다.
7. `2025-08`로 실행해 청구서 PDF를 만들었다.
8. `PB_Make_Bill.py`에 연도·월 선택 대화 상자를 추가했다. 인자 없이 실행하면 대화 상자가 열리고, 인자가 있으면 기존처럼 바로 처리한다.

## 실행 방법

인자 없이 실행하면 연도와 월을 고르는 대화 상자가 열립니다.

```powershell
.\.venv\Scripts\python.exe .\PB_Make_Bill.py
```

대화 상자 없이 연월을 지정하려면:

```powershell
.\.venv\Scripts\python.exe .\PB_Make_Bill.py 2025-08
```

LibreOffice가 필요합니다. 기본 경로:

`C:\Program Files\LibreOffice\program\soffice.exe`

## 실행 결과 (2025-08)

- 대상 연월: 2025-08
- 작성 시트: 67개
- 건너뛴 거래처: 0개
- PDF 67개: [resData/PDF](../resData/PDF)
- 시트명 예: `수원상사_2508`, 중복 시 `서울서비스_2508_2`
- `청구서.xlsx`는 원본 3개 시트만 유지

## 처리 흐름 요약

1. 연월 선택 대화 상자(또는 `yyyy-mm` 인자)로 대상 월을 정한다.
2. `매출.xlsx`의 `매출`·`거래처`, `청구서.xlsx`의 `청구서` 시트를 확인한다.
3. 매출일(A)이 해당 월인 행만 고른다.
4. 거래처코드로 마스터를 찾고, 없으면 경고 후 건너뛴다.
5. `청구서` 시트를 복사해 머리글과 품목을 채운다.
6. 거래처 시트만 담긴 임시 엑셀을 만들고 LibreOffice로 PDF로 변환한다.
7. 거래처 시트를 삭제하고 원본 3개 시트만 남긴다.

상세 분기는 [B02Bill_flow.md](B02Bill_flow.md), 호출 순서는 [B03Bill_sequence.md](B03Bill_sequence.md)를 참고합니다.

## 프로젝트 구조

```text
ex08maechulManager/
  PB_Make_Bill.py
  PA_CSV_to_Excel.py
  import_sales.py
  requirements.txt
  .venv/
  docs/
    B01Bill.md
    B02Bill_flow.md
    B03Bill_sequence.md
    B04Bill_readme.md
  resData/
    매출.xlsx
    청구서.xlsx
    PDF/
      수원상사_2508.pdf ...
```
