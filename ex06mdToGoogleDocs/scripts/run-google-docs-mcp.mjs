import { readFileSync, existsSync } from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const defaultRepoRoot = path.resolve(scriptDir, "../..");
const repoRoot = process.env.REPO_ROOT?.trim() || defaultRepoRoot;
const credPath =
  process.env.CREDENTIALS_PATH?.trim() || path.join(repoRoot, "credentials.json");

if (!existsSync(credPath)) {
  console.error(
    `credentials.json not found: ${credPath}\nCopy credentials.json.example to credentials.json and fill in OAuth values.`,
  );
  process.exit(1);
}

const creds = JSON.parse(readFileSync(credPath, "utf8"));
const installed = creds.installed ?? creds.web;
const clientId = installed?.client_id;
const clientSecret = installed?.client_secret;

if (!clientId || !clientSecret) {
  console.error("credentials.json must contain client_id and client_secret.");
  process.exit(1);
}

const npx = process.env.NPX_COMMAND ?? "npx";
const child = spawn(npx, ["-y", "@a-bonus/google-docs-mcp"], {
  stdio: "inherit",
  env: {
    ...process.env,
    GOOGLE_CLIENT_ID: clientId,
    GOOGLE_CLIENT_SECRET: clientSecret,
    XDG_CONFIG_HOME: process.env.XDG_CONFIG_HOME?.trim() || repoRoot,
  },
  shell: true,
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 1);
});
