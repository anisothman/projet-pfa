import type { AnalysisReport, CandidatesResponse, ProgressEvent } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function fetchReport(id: string): Promise<AnalysisReport | null> {
  const res = await fetch(`${API_URL}/reports/${id}`, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Failed to load report: ${res.status}`);
  return res.json();
}

export function reportPdfUrl(id: string): string {
  return `${API_URL}/reports/${id}/pdf`;
}

export async function fetchCandidates(
  company: string,
  city: string | null,
  signal?: AbortSignal,
): Promise<CandidatesResponse> {
  const res = await fetch(`${API_URL}/candidates`, {
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

/**
 * S'abonne à /analyze/stream via SSE. EventSource du navigateur ne supporte pas le POST,
 * on utilise donc fetch + lecture du ReadableStream. Chaque évènement SSE est mappé sur un ProgressEvent.
 */
export async function analyzeStream(
  company: string,
  city: string | null,
  onEvent: (evt: ProgressEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const resp = await fetch(`${API_URL}/analyze/stream`, {
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
    // On normalise les fins de ligne Windows (\r\n) car sse-starlette les utilise par défaut,
    // sinon la recherche de séparateur de frame "\n\n" ne matche jamais.
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
        // on ignore les heartbeats ou les frames mal formées
      }
    }
  }
}
