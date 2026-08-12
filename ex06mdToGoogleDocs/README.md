# ex06mdToGoogleDocs

Markdown 파일을 Google Docs에 자동 등록하는 TypeScript 워커.

## 사전 준비 (Google Cloud)

서비스 계정 프로젝트(`my-cursor-mcp-505302`)에서 다음 API를 **활성화**해야 합니다.

1. [Google Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com)
2. [Google Docs API](https://console.cloud.google.com/apis/library/docs.googleapis.com)

Service Account 사용 시 생성된 Doc/Drive 폴더를 서비스 계정 이메일에 **Editor**로 공유하세요.

## 설정

```powershell
cd ex06mdToGoogleDocs
copy .env.example .env
copy ..\credentials.json.example ..\credentials.json
# credentials.json 에 OAuth client_id / client_secret 입력
npm install
npm run auth
```

## 실행

```powershell
# job/*.md 1회 처리
npm run once

# job/*.md 감시
npm run watch
```

## 폴더

| 경로 | 용도 |
|------|------|
| `job/` | 처리 대기 MD |
| `job/processing/` | 처리 중 |
| `job/completed/` | 성공 |
| `job/failed/` | 실패 + `.error.log` |

## MCP (Cursor)

[`.cursor/mcp.json`](.cursor/mcp.json) — MCP 서버 `google-drive-docs`, OAuth는 `scripts/run-google-docs-mcp.mjs`가 `credentials.json`에서 로드.

사양: [`docs/SPEC-md-to-gdocs.md`](docs/SPEC-md-to-gdocs.md)
