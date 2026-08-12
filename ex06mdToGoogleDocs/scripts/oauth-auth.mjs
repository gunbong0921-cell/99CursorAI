import { copyFileSync, existsSync, mkdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const credPath = process.env.CREDENTIALS_PATH?.trim() || path.join(repoRoot, "credentials.json");
const rootTokenPath = path.join(repoRoot, "token.json");
const mcpTokenPath = path.join(repoRoot, "google-docs-mcp", "token.json");
const legacyTokenPaths = [
  path.join(process.env.USERPROFILE ?? "", ".config", "google-docs-mcp", "token.json"),
  path.join(process.env.USERPROFILE ?? "", ".config", "google-docs-mcp", "md-to-gdocs-mcp", "token.json"),
];

function syncRootToMcp() {
  if (!existsSync(rootTokenPath)) {
    return;
  }
  mkdirSync(path.dirname(mcpTokenPath), { recursive: true });
  copyFileSync(rootTokenPath, mcpTokenPath);
}

function syncMcpToRoot() {
  if (!existsSync(mcpTokenPath)) {
    return;
  }
  copyFileSync(mcpTokenPath, rootTokenPath);
}

function migrateLegacyToken() {
  if (existsSync(rootTokenPath)) {
    return;
  }

  for (const legacyPath of legacyTokenPaths) {
    if (existsSync(legacyPath)) {
      copyFileSync(legacyPath, rootTokenPath);
      console.log("Migrated token to", rootTokenPath);
      return;
    }
  }
}

if (!existsSync(credPath)) {
  console.error("credentials.json not found:", credPath);
  process.exit(1);
}

const creds = JSON.parse(readFileSync(credPath, "utf8"));
const clientId = creds.installed?.client_id;
const clientSecret = creds.installed?.client_secret;

if (!clientId || !clientSecret) {
  console.error("credentials.json must contain installed.client_id and client_secret");
  process.exit(1);
}

migrateLegacyToken();
syncRootToMcp();

const npx = process.env.NPX_COMMAND ?? "npx";
const result = spawnSync(npx, ["-y", "@a-bonus/google-docs-mcp", "auth"], {
  stdio: "inherit",
  env: {
    ...process.env,
    GOOGLE_CLIENT_ID: clientId,
    GOOGLE_CLIENT_SECRET: clientSecret,
    XDG_CONFIG_HOME: repoRoot,
  },
  shell: true,
});

syncMcpToRoot();

if (result.status === 0) {
  console.log("OAuth token saved to", rootTokenPath);
}

process.exit(result.status ?? 1);
