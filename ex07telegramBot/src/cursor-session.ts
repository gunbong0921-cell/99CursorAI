import { Agent, CursorAgentError, type SDKAgent } from "@cursor/sdk";
import { config } from "./config.js";
import { log } from "./log.js";

const TELEGRAM_CHAR_LIMIT = 4000;

const SYSTEM_HINT = [
  "You are connected through a Telegram bridge.",
  "The user message below arrived from Telegram.",
  "Reply in Korean unless the user writes in another language.",
  "Do not call Telegram send-message or send-photo tools.",
  "Your text reply is forwarded to Telegram automatically.",
  "Keep the answer readable on a phone unless the user asks for more detail.",
].join(" ");

export class CursorSession {
  private agent: SDKAgent | undefined;
  private queue: Promise<void> = Promise.resolve();

  async send(userText: string): Promise<string> {
    const run = this.queue.then(() => this.runTurn(userText));
    this.queue = run.then(
      () => undefined,
      () => undefined,
    );
    return run;
  }

  async reset(): Promise<void> {
    await this.dispose();
  }

  async dispose(): Promise<void> {
    if (!this.agent) {
      return;
    }
    const agent = this.agent;
    this.agent = undefined;
    await agent[Symbol.asyncDispose]();
  }

  private async runTurn(userText: string): Promise<string> {
    const agent = await this.ensureAgent();
    const prompt = `${SYSTEM_HINT}\n\nUser message:\n${userText}`;

    try {
      log("Cursor", "프롬프트 전송");
      const run = await agent.send(prompt);
      log("Cursor", `runId=${run.id}`);
      const result = await run.wait();

      if (result.status === "error") {
        throw new Error(result.error?.message ?? `Cursor run failed (${result.id})`);
      }

      if (result.status === "cancelled") {
        throw new Error("Cursor run was cancelled");
      }

      const text = result.result?.trim();
      return text || "(Cursor returned an empty reply)";
    } catch (error) {
      if (error instanceof CursorAgentError) {
        throw new Error(`Cursor startup failed: ${error.message}`);
      }
      throw error;
    }
  }

  private async ensureAgent(): Promise<SDKAgent> {
    if (this.agent) {
      return this.agent;
    }

    log("Cursor", "세션 생성 중...");
    this.agent = await Agent.create({
      apiKey: config.cursorApiKey,
      model: { id: config.cursorModel },
      local: {
        cwd: config.cursorWorkspace,
        settingSources: ["project"],
      },
    });
    log("Cursor", `세션 준비 agentId=${this.agent.agentId}`);

    return this.agent;
  }
}

export function splitTelegramText(text: string): string[] {
  if (text.length <= TELEGRAM_CHAR_LIMIT) {
    return [text];
  }

  const chunks: string[] = [];
  let remaining = text;

  while (remaining.length > TELEGRAM_CHAR_LIMIT) {
    const window = remaining.slice(0, TELEGRAM_CHAR_LIMIT);
    const breakAt = window.lastIndexOf("\n") > 0 ? window.lastIndexOf("\n") : TELEGRAM_CHAR_LIMIT;
    chunks.push(remaining.slice(0, breakAt).trimEnd());
    remaining = remaining.slice(breakAt).trimStart();
  }

  if (remaining) {
    chunks.push(remaining);
  }

  return chunks;
}
