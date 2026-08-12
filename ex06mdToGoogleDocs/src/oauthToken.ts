import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import path from "node:path";

export function getOAuthTokenPaths(repoRoot: string) {
  return {
    repoRoot,
    rootTokenPath: path.join(repoRoot, "token.json"),
    mcpTokenPath: path.join(repoRoot, "google-docs-mcp", "token.json"),
  };
}

export function syncOAuthTokenToMcp(repoRoot: string): void {
  const { rootTokenPath, mcpTokenPath } = getOAuthTokenPaths(repoRoot);
  if (!existsSync(rootTokenPath)) {
    return;
  }

  mkdirSync(path.dirname(mcpTokenPath), { recursive: true });
  copyFileSync(rootTokenPath, mcpTokenPath);
}

export function syncOAuthTokenToRoot(repoRoot: string): void {
  const { rootTokenPath, mcpTokenPath } = getOAuthTokenPaths(repoRoot);
  if (!existsSync(mcpTokenPath)) {
    return;
  }

  copyFileSync(mcpTokenPath, rootTokenPath);
}
