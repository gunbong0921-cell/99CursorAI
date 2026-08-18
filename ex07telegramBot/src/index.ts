import { startBridge, stopBridge } from "./telegram-bridge.js";
import { log } from "./log.js";

const bot = await startBridge();

async function shutdown(signal: string): Promise<void> {
  log("종료", signal);
  await stopBridge(bot);
  process.exit(0);
}

process.on("SIGINT", () => {
  void shutdown("SIGINT");
});
process.on("SIGTERM", () => {
  void shutdown("SIGTERM");
});
