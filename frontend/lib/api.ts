import type { AnalysisReport, CandidatesResponse, ProgressEvent } from "@/lib/types";

const BROWSER_API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SERVER_API_URL = process.env.API_INTERNAL_URL ?? BROWSER_API_URL;

function baseUrl(): string {
  return typeof window === "undefined" ? SERVER_API_URL : BROWSER_API_URL;
}

export async function fetchReport(id: string): Promise<AnalysisReport | null> {
  const res = await fetch(`${baseUrl()}/reports/${id}`, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Failed to load report: ${res.status}`);
  return res.json();
}

export function reportPdfUrl(id: string): string {
  return `${BROWSER_API_URL}/reports/${id}/pdf`;
}

export async function fetchCandidates(
  company: string,
  city: string | null,
  signal?: AbortSignal,
): Promise<CandidatesResponse> {
  const res = await fetch(`${BROWSER_API_URL}/candidates`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ company, city: city || null }),
    signal,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Recherche échouée (${res.status})`);
  }
  return res.json();
}

export async function analyzeStream(
  company: string,
  city: string | null,
  onEvent: (evt: ProgressEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const resp = await fetch(`${BROWSER_API_URL}/analyze/stream`, {
    method: "POST",
    headers: { "content-type": "application/json", accept: "text/event-stream" },
    body: JSON.stringify({ company, city: city || null }),
    signal,
  });
  if (!resp.ok || !resp.body) throw new Error(`Stream failed: ${resp.status}`);

  const reader = resp.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += value.replace(/\r\n/g, "\n");
    let idx;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const dataLine = frame.split("\n").find((l) => l.startsWith("data:"));
      if (!dataLine) continue;
      const payload = dataLine.slice(5).trim();
      try {
        onEvent(JSON.parse(payload) as ProgressEvent);
      } catch {
        // ignore heartbeats / malformed
      }
    }
  }
}