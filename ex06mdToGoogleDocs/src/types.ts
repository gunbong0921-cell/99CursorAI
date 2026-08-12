export type AuthMode = "oauth" | "service_account";

export interface ManifestEntry {
  filename: string;
  docId: string;
  docUrl: string;
  title: string;
  processedAt: string;
  authMode: AuthMode;
}

export interface PublishResult {
  docId: string;
  docUrl: string;
  title: string;
  authMode: AuthMode;
}

export interface ParsedMarkdown {
  title: string;
  content: string;
}
