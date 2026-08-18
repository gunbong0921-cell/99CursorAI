# ex07 Telegram Bot

Telegram 메시지를 Cursor Agent로 전달하고, 답변을 Telegram으로 돌려주는 브릿지 봇입니다.

## 기능

- Telegram 텍스트 → Cursor Agent 전달
- Agent 응답 → Telegram 자동 회신 (4000자 초과 시 분할)
- 허용된 사용자만 사용 가능
- `/reset` — Cursor 대화 세션 초기화
- 긴 답변은 줄 단위로 나눠 전송

## 요구 사항

- Node.js **22.13.0** 이상
- Telegram Bot Token ([@BotFather](https://t.me/BotFather))
- Cursor API Key

## 설치

```bash
npm install
```

## 환경 변수

`.env.example`을 복사해 `.env` 또는 `.env/.env` 파일을 만듭니다.

| 변수 | 필수 | 설명 |
|------|------|------|
| `TELEGRAM_BOT_API_TOKEN` | ✅ | Telegram 봇 토큰 |
| `TELEGRAM_ALLOWED_USER_ID` | ✅ | 허용할 Telegram 사용자 ID |
| `CURSOR_API_KEY` | ✅ | Cursor API 키 |
| `CURSOR_WORKSPACE` | | Agent 작업 디렉터리 (기본: 프로젝트 루트) |
| `CURSOR_MODEL` | | 사용할 모델 (기본: `composer-2.5`) |

Telegram 사용자 ID는 [@userinfobot](https://t.me/userinfobot) 등으로 확인할 수 있습니다.

## 실행

```bash
# 일반 실행
npm start

# 개발 (파일 변경 시 자동 재시작)
npm run dev

# 타입 검사
npm run typecheck
```

종료: `Ctrl+C`

## Telegram 명령

| 명령 | 설명 |
|------|------|
| `/start` | 봇 안내 메시지 |
| `/reset` | Cursor 세션 초기화 |

일반 텍스트 메시지는 Cursor Agent에게 전달됩니다.

## 프로젝트 구조

```
src/
├── index.ts           # 진입점
├── telegram-bridge.ts # Telegram 봇 (grammy)
├── cursor-session.ts  # Cursor Agent 세션
├── config.ts          # 환경 변수
└── log.ts             # 로그 유틸
```

## 동작 흐름

```
Telegram 메시지
    ↓
허용 사용자 확인
    ↓
Cursor Agent (세션 유지)
    ↓
응답 분할 → Telegram 회신
```

## 주의

- `.env` 파일은 Git에 올리지 마세요.
- 허용되지 않은 사용자의 메시지는 무시됩니다.
- 한 번에 하나의 메시지만 순차 처리됩니다.
