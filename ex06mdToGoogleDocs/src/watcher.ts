import chokidar, { type FSWatcher } from "chokidar";
import path from "node:path";
import { config } from "./config.js";
import { isJobMarkdown } from "./moveFile.js";
import { processMarkdownFile } from "./pipeline.js";

const processing = new Set<string>();

function isIgnoredSubdir(filePath: string): boolean {
  const relative = path.relative(config.jobDir, filePath);
  if (!relative || relative.startsWith("..")) {
    return true;
  }

  const topSegment = relative.split(path.sep)[0];
  return topSegment === "processing" || topSegment === "completed" || topSegment === "failed";
}

async function handleFile(filePath: string, event: string): Promise<void> {
  if (isIgnoredSubdir(filePath) || !isJobMarkdown(filePath) || processing.has(filePath)) {
    return;
  }

  processing.add(filePath);
  try {
    console.log(`[watch] detected ${event}: ${path.basename(filePath)}`);
    await processMarkdownFile(filePath);
  } catch (error) {
    console.error(`[watch] error processing ${path.basename(filePath)}:`, error);
  } finally {
    processing.delete(filePath);
  }
}

export function startWatcher(): FSWatcher {
  console.log(`[watch] watching ${config.jobDir} (copy *.md here to auto-convert)`);

  const watcher = chokidar.watch(config.jobDir, {
    depth: 0,
    ignoreInitial: false,
    ignored: [
      path.join(config.jobDir, "processing"),
      path.join(config.jobDir, "completed"),
      path.join(config.jobDir, "failed"),
    ],
    awaitWriteFinish: {
      stabilityThreshold: 1000,
      pollInterval: 200,
    },
  });

  const onDetected = (event: "add" | "change") => (filePath: string) => {
    void handleFile(filePath, event);
  };

  watcher.on("add", onDetected("add"));
  watcher.on("change", onDetected("change"));
  watcher.on("error", (error) => {
    console.error("[watch] watcher error:", error);
  });

  return watcher;
}
