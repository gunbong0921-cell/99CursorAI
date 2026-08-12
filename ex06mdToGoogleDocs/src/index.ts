import { ensureJobDirs } from "./moveFile.js";
import { processJobDirectory } from "./pipeline.js";
import { startWatcher } from "./watcher.js";

async function main(): Promise<void> {
  const mode = process.argv[2] ?? "once";
  await ensureJobDirs();

  if (mode === "watch") {
    const watcher = startWatcher();
    console.log("[main] watch mode started — drop .md files into job/ to convert");

    const shutdown = async () => {
      console.log("\n[main] shutting down watcher...");
      await watcher.close();
      process.exit(0);
    };

    process.on("SIGINT", () => void shutdown());
    process.on("SIGTERM", () => void shutdown());
    return;
  }

  const count = await processJobDirectory();
  console.log(`[main] processed ${count} file(s)`);
}

main().catch((error) => {
  console.error("[main] fatal error:", error);
  process.exit(1);
});
