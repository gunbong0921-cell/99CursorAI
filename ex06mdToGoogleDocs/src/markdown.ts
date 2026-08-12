import path from "node:path";
import type { ParsedMarkdown } from "./types.js";

export function parseMarkdownFile(filePath: string, raw: string): ParsedMarkdown {
  const fallbackTitle = path.basename(filePath, path.extname(filePath));
  const headingMatch = raw.match(/^#\s+(.+)$/m);
  const title = headingMatch?.[1]?.trim() || fallbackTitle;
  return { title, content: raw.trim() };
}
