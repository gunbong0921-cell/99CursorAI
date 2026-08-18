export function now(): string {
  return new Date().toLocaleString("sv-SE", { timeZone: "Asia/Seoul" });
}

export function log(...parts: unknown[]): void {
  console.log(`[${now()}]`, ...parts);
}
