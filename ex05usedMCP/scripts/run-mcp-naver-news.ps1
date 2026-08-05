$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $projectRoot ".env"

if (Test-Path $envFile) {
  Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#")) { return }
    $parts = $line -split "=", 2
    if ($parts.Count -ne 2) { return }
    $name = $parts[0].Trim()
    $value = $parts[1].Trim().Trim('"').Trim("'")
    [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
  }
}

# Support both NAVER_* and X_NAVER_* names from template configs
if (-not $env:NAVER_CLIENT_ID -and $env:X_NAVER_CLIENT_ID) {
  $env:NAVER_CLIENT_ID = $env:X_NAVER_CLIENT_ID
}
if (-not $env:NAVER_CLIENT_SECRET -and $env:X_NAVER_CLIENT_SECRET) {
  $env:NAVER_CLIENT_SECRET = $env:X_NAVER_CLIENT_SECRET
}

if (-not $env:NAVER_CLIENT_ID -or -not $env:NAVER_CLIENT_SECRET -or
    $env:NAVER_CLIENT_ID -match "YOUR_|your_naver" -or
    $env:NAVER_CLIENT_SECRET -match "YOUR_|your_naver") {
  Write-Error @"
NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 가 설정되지 않았습니다.
1) https://developers.naver.com/apps/#/register 에서 앱 등록 (검색 API 활성화)
2) 프로젝트 루트의 .env.example 을 .env 로 복사
3) Client ID / Client Secret 입력 후 Cursor에서 MCP를 새로고침
"@
  exit 1
}

npx -y naver-news-mcp
