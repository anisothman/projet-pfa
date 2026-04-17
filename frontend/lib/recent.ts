const KEY = "localis:recent";
const MAX = 5;

export interface RecentEntry {
  id: string;
  company: string;
  ts: number;
}

export function getRecent(): RecentEntry[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(window.localStorage.getItem(KEY) ?? "[]") as RecentEntry[];
  } catch {
    return [];
  }
}

export function addRecent(entry: RecentEntry): void {
  if (typeof window === "undefined") return;
  const existing = getRecent().filter((e) => e.id !== entry.id);
  const next = [entry, ...existing].slice(0, MAX);
  window.localStorage.setItem(KEY, JSON.stringify(next));
}

export function clearRecent(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(KEY);
}
