import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import path from "node:path";
import { config } from "./config.js";
import type { ManifestEntry } from "./types.js";

async function ensureDir(dirPath: string): Promise<void> {
  await mkdir(dirPath, { recursive: true });
}

export async function ensureJobDirs(): Promise<void> {
  await Promise.all([
    ensureDir(config.jobDir),
    ensureDir(config.completedDir),
    ensureDir(config.failedDir),
    ensureDir(config.processingDir),
  ]);
}

async function readManifest(): Promise<ManifestEntry[]> {
  try {
    const raw = await readFile(config.manifestPath, "utf8");
    return JSON.parse(raw) as ManifestEntry[];
  } catch {
    return [];
  }
}

export async function appendManifest(entry: ManifestEntry): Promise<void> {
  const entries = await readManifest();
  entries.push(entry);
  await writeFile(config.manifestPath, `${JSON.stringify(entries, null, 2)}\n`, "utf8");
}

export async function moveToProcessing(sourcePath: string): Promise<string> {
  const fileName = path.basename(sourcePath);
  const targetPath = path.join(config.processingDir, fileName);
  await rename(sourcePath, targetPath);
  return targetPath;
}

export async function moveToCompleted(processingPath: string): Promise<string> {
  const fileName = path.basename(processingPath);
  const targetPath = path.join(config.completedDir, fileName);
  await rename(processingPath, targetPath);
  return targetPath;
}

export async function moveToFailed(processingPath: string, error: unknown): Promise<string> {
  const fileName = path.basename(processingPath);
  const targetPath = path.join(config.failedDir, fileName);
  const logPath = `${targetPath}.error.log`;
  await rename(processingPath, targetPath);
  await writeFile(
    logPath,
    `${new Date().toISOString()}\n${error instanceof Error ? error.stack ?? error.message : String(error)}\n`,
    "utf8",
  );
  return targetPath;
}

export function isJobMarkdown(filePath: string): boolean {
  const fileName = path.basename(filePath);
  if (!fileName.endsWith(".md")) {
    return false;
  }

  const parentDir = path.dirname(filePath);
  return path.resolve(parentDir) === path.resolve(config.jobDir);
}
