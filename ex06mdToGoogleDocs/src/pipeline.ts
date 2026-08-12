import { readFile } from "node:fs/promises";
import path from "node:path";
import { config } from "./config.js";
import { publishMarkdownDocument } from "./docsPublisher.js";
import { parseMarkdownFile } from "./markdown.js";
import {
  appendManifest,
  moveToCompleted,
  moveToFailed,
  moveToProcessing,
} from "./moveFile.js";

export async function processMarkdownFile(sourcePath: string): Promise<void> {
  const fileName = path.basename(sourcePath);
  let processingPath = sourcePath;

  try {
    processingPath = await moveToProcessing(sourcePath);
    const raw = await readFile(processingPath, "utf8");
    const parsed = parseMarkdownFile(processingPath, raw);

    console.log(`[pipeline] publishing ${fileName} as "${parsed.title}"`);
    const result = await publishMarkdownDocument(parsed.title, parsed.content);

    await appendManifest({
      filename: fileName,
      docId: result.docId,
      docUrl: result.docUrl,
      title: result.title,
      processedAt: new Date().toISOString(),
      authMode: result.authMode,
    });

    await moveToCompleted(processingPath);
    console.log(`[pipeline] completed ${fileName} -> ${result.docUrl}`);
  } catch (error) {
    console.error(`[pipeline] failed ${fileName}:`, error);
    if (processingPath !== sourcePath) {
      await moveToFailed(processingPath, error);
    }
    throw error;
  }
}

export async function processJobDirectory(): Promise<number> {
  const { readdir } = await import("node:fs/promises");
  const entries = await readdir(config.jobDir);
  const mdFiles = entries
    .filter((name) => name.endsWith(".md"))
    .map((name) => path.join(config.jobDir, name));

  for (const filePath of mdFiles) {
    await processMarkdownFile(filePath);
  }

  return mdFiles.length;
}
