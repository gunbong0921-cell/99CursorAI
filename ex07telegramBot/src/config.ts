import path from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadDotenv } from "dotenv";

const projectRoot = path.resolve(fileURLToPath(new URL("..", import.meta.url)));

loadDotenv({ path: path.join(projectRoot, ".env", ".env") });
loadDotenv({ path: path.join(projectRoot, ".env") });

function required(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function optional(name: string): string | undefined {
  const value = process.env[name]?.trim();
  return value ? value : undefined;
}

export const config = {
  projectRoot,
  telegramBotToken: required("TELEGRAM_BOT_API_TOKEN"),
  allowedUserId: required("TELEGRAM_ALLOWED_USER_ID"),
  cursorApiKey: required("CURSOR_API_KEY"),
  cursorWorkspace: optional("CURSOR_WORKSPACE") ?? projectRoot,
  cursorModel: optional("CURSOR_MODEL") ?? "composer-2.5",
};
