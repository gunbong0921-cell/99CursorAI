import { Bot, type Context } from "grammy";
import { config } from "./config.js";
import { CursorSession, splitTelegramText } from "./cursor-session.js";
import { log } from "./log.js";

const session = new CursorSession();

function preview(text: string, max = 200): string {
  const compact = text.replace(/\s+/g, " ").trim();
  return compact.length > max ? `${compact.slice(0, max)}…` : compact;
}

function describeUpdate(ctx: Context): string {
  const userId = ctx.from?.id ?? "-";
  const username = ctx.from?.username ? `@${ctx.from.username}` : ctx.from?.first_name ?? "-";
  const chatId = ctx.chat?.id ?? "-";
  const text = ctx.message?.text ?? ctx.message?.caption;
  const kind = text ? "text" : ctx.message?.photo ? "photo" : ctx.message ? "message" : "update";
  const body = text ? preview(text) : kind;
  return `user=${userId} ${username} chat=${chatId} ${kind} "${body}"`;
}

function isAllowed(ctx: Context): boolean {
  return String(ctx.from?.id ?? "") === config.allowedUserId;
}

async function replyParts(ctx: Context, text: string): Promise<void> {
  for (const part of splitTelegramText(text)) {
    await ctx.reply(part);
  }
}

export async function startBridge(): Promise<Bot> {
  const bot = new Bot(config.telegramBotToken);

  bot.use(async (ctx, next) => {
    log("수신", describeUpdate(ctx));
    if (!isAllowed(ctx)) {
      log("무시", `허용되지 않은 사용자 user=${ctx.from?.id ?? "-"} allowed=${config.allowedUserId}`);
    }
    await next();
  });

  bot.command("start", async (ctx) => {
    if (!isAllowed(ctx)) {
      return;
    }
    log("명령", "/start");
    await ctx.reply(
      [
        "Telegram → Cursor 브릿지가 실행 중입니다.",
        "",
        "메시지를 보내면 Cursor Agent에게 전달됩니다.",
        "/reset — 대화 세션을 새로 시작합니다.",
      ].join("\n"),
    );
  });

  bot.command("reset", async (ctx) => {
    if (!isAllowed(ctx)) {
      return;
    }
    log("명령", "/reset");
    await session.reset();
    await ctx.reply("Cursor 세션을 초기화했습니다. 다음 메시지부터 새 대화로 이어집니다.");
  });

  bot.on("message:text", async (ctx) => {
    if (!isAllowed(ctx)) {
      return;
    }

    const text = ctx.message.text.trim();
    if (!text || text.startsWith("/")) {
      return;
    }

    log("전달", `Cursor로 전송 (${text.length}자)`);

    const typing = setInterval(() => {
      void ctx.replyWithChatAction("typing");
    }, 4000);
    void ctx.replyWithChatAction("typing");

    try {
      const reply = await session.send(text);
      log("답장", `Cursor → Telegram (${reply.length}자) "${preview(reply)}"`);
      await replyParts(ctx, reply);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      log("오류", message);
      await ctx.reply(`Cursor 전달에 실패했습니다.\n${message}`);
    } finally {
      clearInterval(typing);
    }
  });

  bot.catch((error) => {
    log("봇오류", error.error);
  });

  await bot.api.deleteWebhook({ drop_pending_updates: false });
  const me = await bot.api.getMe();
  log("시작", `Telegram bot @${me.username} polling`);
  log("설정", `allowedUserId=${config.allowedUserId}`);
  log("설정", `workspace=${config.cursorWorkspace}`);
  log("설정", `model=${config.cursorModel}`);

  void bot.start({
    onStart: () => {
      log("대기", "Telegram → Cursor 브릿지 실행 중. Ctrl+C로 종료");
    },
  });

  return bot;
}

export async function stopBridge(bot: Bot): Promise<void> {
  await bot.stop();
  await session.dispose();
}
