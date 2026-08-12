import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import dotenv from "dotenv";
import type { AuthMode } from "./types.js";
import { resolveGoogleOAuthConfig } from "./googleOAuth.js";

const projectRoot = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
dotenv.config({ path: path.join(projectRoot, ".env"), override: true });

function resolvePath(value: string | undefined, fallback: string): string {
  const target = value?.trim() || fallback;
  return path.isAbsolute(target) ? target : path.resolve(projectRoot, target);
}

function parseAuthMode(value: string | undefined): AuthMode {
  return value === "oauth" ? "oauth" : "service_account";
}

const repoRoot = resolvePath(process.env.REPO_ROOT, path.join(projectRoot, ".."));
const oauth = resolveGoogleOAuthConfig(repoRoot);

export const config = {
  projectRoot,
  repoRoot,
  authMode: parseAuthMode(process.env.AUTH_MODE),
  googleClientId: oauth.clientId,
  googleClientSecret: oauth.clientSecret,
  oauthTokenPath: resolvePath(
    process.env.OAUTH_TOKEN_PATH,
    path.join(repoRoot, "token.json"),
  ),
  xdgConfigHome: resolvePath(process.env.XDG_CONFIG_HOME, repoRoot),
  serviceAccountPath: resolvePath(
    process.env.SERVICE_ACCOUNT_PATH,
    path.join(projectRoot, "..", "symmetric-lore-504707-s0-bc9098aa1ff0.json"),
  ),
  docsFolderId: process.env.DOCS_FOLDER_ID?.trim() || undefined,
  docsTargetDocId: process.env.DOCS_TARGET_DOC_ID?.trim() || undefined,
  jobDir: resolvePath(process.env.JOB_DIR, path.join(projectRoot, "job")),
  completedDir: resolvePath(
    process.env.COMPLETED_DIR,
    path.join(projectRoot, "job", "completed"),
  ),
  failedDir: resolvePath(process.env.FAILED_DIR, path.join(projectRoot, "job", "failed")),
  processingDir: resolvePath(
    process.env.PROCESSING_DIR,
    path.join(projectRoot, "job", "processing"),
  ),
  manifestPath: resolvePath(
    process.env.MANIFEST_PATH,
    path.join(projectRoot, "job", "completed", ".manifest.json"),
  ),
  npxCommand: process.env.NPX_COMMAND ?? "npx",
};

export function getServiceAccountEmail(): string {
  try {
    const raw = readFileSync(config.serviceAccountPath, "utf8");
    const parsed = JSON.parse(raw) as { client_email?: string };
    return parsed.client_email ?? "unknown-service-account";
  } catch {
    return "unknown-service-account";
  }
}

export function assertServiceAccountDestination(): void {
  if (config.authMode !== "service_account") {
    return;
  }

  if (config.docsFolderId || config.docsTargetDocId) {
    return;
  }

  const email = getServiceAccountEmail();
  throw new Error(
    [
      "Service Account 모드에서는 Google Docs 생성 위치가 필요합니다.",
      "",
      "방법 1) Drive 폴더 공유 (권장)",
      `  - Google Drive에 폴더 생성 후 ${email} 에 Editor 권한 부여`,
      "  - .env 에 DOCS_FOLDER_ID=<폴더ID> 설정",
      "",
      "방법 2) 기존 Doc 공유 (테스트용)",
      "  - 빈 Google Doc 생성 후 같은 이메일에 Editor 권한 부여",
      "  - .env 에 DOCS_TARGET_DOC_ID=<문서ID> 설정",
      "",
      "설정 후: npm run once",
    ].join("\n"),
  );
}
