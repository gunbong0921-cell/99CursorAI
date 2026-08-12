import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { config } from "./config.js";
import { syncOAuthTokenToMcp } from "./oauthToken.js";

function buildMcpEnv(): Record<string, string> {
  const env: Record<string, string> = {
    AUTH_MODE: config.authMode,
    PYTHONIOENCODING: "utf-8",
    XDG_CONFIG_HOME: config.xdgConfigHome,
  };

  if (config.authMode === "oauth") {
    env.GOOGLE_CLIENT_ID = config.googleClientId;
    env.GOOGLE_CLIENT_SECRET = config.googleClientSecret;
  } else {
    env.SERVICE_ACCOUNT_PATH = config.serviceAccountPath;
  }

  return env;
}

function extractText(result: unknown): string {
  if (!result || typeof result !== "object") {
    return "";
  }

  const content = (result as { content?: Array<{ type?: string; text?: string }> }).content;
  if (!Array.isArray(content)) {
    return JSON.stringify(result);
  }

  return content
    .filter((item) => item.type === "text" && item.text)
    .map((item) => item.text)
    .join("\n");
}

function parseJsonPayload(text: string): unknown {
  const trimmed = text.trim();
  if (!trimmed) {
    return {};
  }

  try {
    return JSON.parse(trimmed);
  } catch {
    const match = trimmed.match(/\{[\s\S]*\}/);
    if (match) {
      return JSON.parse(match[0]);
    }
    return { raw: trimmed };
  }
}

export class DocsMcpClient {
  private client: Client | null = null;
  private transport: StdioClientTransport | null = null;

  async connect(): Promise<void> {
    const mcpEnv = {
      ...process.env,
      ...buildMcpEnv(),
    } as Record<string, string>;

    if (config.authMode === "oauth") {
      delete mcpEnv.SERVICE_ACCOUNT_PATH;
      delete mcpEnv.GOOGLE_MCP_PROFILE;
      syncOAuthTokenToMcp(config.repoRoot);
    }

    this.transport = new StdioClientTransport({
      command: config.npxCommand,
      args: ["-y", "@a-bonus/google-docs-mcp"],
      env: mcpEnv,
    });

    this.client = new Client(
      { name: "md-to-gdocs-mcp", version: "1.0.0" },
      { enforceStrictCapabilities: false },
    );
    await this.client.connect(this.transport);
  }

  async listTools(): Promise<string[]> {
    if (!this.client) {
      throw new Error("MCP client is not connected");
    }
    const tools = await this.client.listTools();
    return tools.tools.map((tool) => tool.name);
  }

  async callTool(name: string, args: Record<string, unknown>): Promise<unknown> {
    if (!this.client) {
      throw new Error("MCP client is not connected");
    }

    const result = await this.client.callTool({ name, arguments: args });
    const text = extractText(result);
    return parseJsonPayload(text);
  }

  async close(): Promise<void> {
    await this.client?.close();
    this.client = null;
    this.transport = null;
  }
}

export function pickDocumentId(payload: unknown): string | undefined {
  if (!payload || typeof payload !== "object") {
    return undefined;
  }

  const record = payload as Record<string, unknown>;
  const candidates = [record.documentId, record.id, record.docId];
  for (const candidate of candidates) {
    if (typeof candidate === "string" && candidate.length > 0) {
      return candidate;
    }
  }
  return undefined;
}
