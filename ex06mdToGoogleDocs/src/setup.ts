import { getServiceAccountEmail } from "./config.js";

const email = getServiceAccountEmail();

console.log("=== MD → Google Docs 설정 안내 ===");
console.log("");
console.log("Service Account:", email);
console.log("");
console.log("Google Docs 자동 생성을 위해 아래 중 하나를 설정하세요.");
console.log("");
console.log("[방법 1] Drive 폴더 공유 (권장)");
console.log("  1. Google Drive에서 새 폴더 생성 (예: MCP-Docs)");
console.log(`  2. ${email} 에 Editor 권한 부여`);
console.log("  3. 폴더 URL의 ID를 .env DOCS_FOLDER_ID 에 입력");
console.log("");
console.log("[방법 2] 기존 Doc 공유 (테스트용)");
console.log("  1. 빈 Google Doc 생성");
console.log(`  2. ${email} 에 Editor 권한 부여`);
console.log("  3. 문서 URL의 ID를 .env DOCS_TARGET_DOC_ID 에 입력");
console.log("");
console.log("설정 후: npm run once");
