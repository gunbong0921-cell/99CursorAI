import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

export function loadGoogleOAuthCredentials(repoRoot: string): {
  clientId: string;
  clientSecret: string;
} | null {
  const credPath =
    process.env.CREDENTIALS_PATH?.trim() || path.join(repoRoot, "credentials.json");

  if (!existsSync(credPath)) {
    return null;
  }

  try {
    const creds = JSON.parse(readFileSync(credPath, "utf8")) as {
      installed?: { client_id?: string; client_secret?: string };
      web?: { client_id?: string; client_secret?: string };
    };
    const key = creds.installed ?? creds.web;
    const clientId = key?.client_id?.trim();
    const clientSecret = key?.client_secret?.trim();
    if (!clientId || !clientSecret) {
      return null;
    }
    return { clientId, clientSecret };
  } catch {
    return null;
  }
}

export function resolveGoogleOAuthConfig(repoRoot: string): {
  clientId: string;
  clientSecret: string;
} {
  const fromEnv = {
    clientId: process.env.GOOGLE_CLIENT_ID?.trim() ?? "",
    clientSecret: process.env.GOOGLE_CLIENT_SECRET?.trim() ?? "",
  };

  if (fromEnv.clientId && fromEnv.clientSecret) {
    return fromEnv;
  }

  const fromFile = loadGoogleOAuthCredentials(repoRoot);
  if (fromFile) {
    return fromFile;
  }

  return fromEnv;
}
