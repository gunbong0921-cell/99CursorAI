import { ensureJobDirs } from "./moveFile.js";
import { processJobDirectory } from "./pipeline.js";
import { startWatcher } from "./watcher.js";

async function main(): Promise<void> {
  const mode = process.argv[2] ?? "once";
  await ensureJobDirs();

  if (mode === "watch") {
    startWatcher();
    console.log("[main] watch mode started");
    return;
  }

  const count = await processJobDirectory();
  console.log(`[main] processed ${count} file(s)`);
}

main().catch((error) => {
  console.error("[main] fatal error:", error);
  process.exit(1);
});
