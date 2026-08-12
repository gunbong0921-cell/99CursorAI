import chokidar, { type FSWatcher } from "chokidar";
import path from "node:path";
import { config } from "./config.js";
import { isJobMarkdown } from "./moveFile.js";
import { processMarkdownFile } from "./pipeline.js";

const processing = new Set<string>();

async function handleFile(filePath: string): Promise<void> {
  if (!isJobMarkdown(filePath) || processing.has(filePath)) {
    return;
  }

  processing.add(filePath);
  try {
    await processMarkdownFile(filePath);
  } finally {
    processing.delete(filePath);
  }
}

export function startWatcher(): FSWatcher {
  const pattern = path.join(config.jobDir, "*.md");
  console.log(`[watch] watching ${pattern}`);

  const watcher = chokidar.watch(pattern, {
    ignoreInitial: false,
    awaitWriteFinish: {
      stabilityThreshold: 1000,
      pollInterval: 200,
    },
  });

  watcher.on("add", (filePath) => {
    void handleFile(filePath);
  });

  return watcher;
}
