import type { SSEEvent, Project, LLMSettings } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002";

export async function wakeServer(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(30000) });
    return res.ok;
  } catch {
    return false;
  }
}

export async function getProjects(): Promise<Project[]> {
  try {
    const res = await fetch(`${API_BASE}/api/projects`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.projects || [];
  } catch {
    return [];
  }
}

export async function indexProject(path: string, name?: string): Promise<{
  success: boolean;
  data?: Record<string, unknown>;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE}/api/index`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path, name }),
    });
    const data = await res.json();
    if (data.error) return { success: false, error: data.error };
    return { success: true, data };
  } catch (e) {
    return { success: false, error: String(e) };
  }
}

export async function startSearch(
  query: string,
  project: string,
  sessionId: string | null,
  onEvent: (event: SSEEvent) => void,
  llmSettings?: LLMSettings,
): Promise<void> {
  const body: Record<string, unknown> = { query, project, session_id: sessionId };
  if (llmSettings?.apiKey) {
    body.provider = llmSettings.provider;
    body.api_key = llmSettings.apiKey;
  } else if (llmSettings?.provider) {
    body.provider = llmSettings.provider;
  }

  const response = await fetch(`${API_BASE}/api/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Network error" }));
    onEvent({ type: "error", content: error.detail || "Failed to start search" });
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    onEvent({ type: "error", content: "No response stream" });
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data: SSEEvent = JSON.parse(line.slice(6));
          onEvent(data);
        } catch {
          // Skip malformed SSE lines
        }
      }
    }
  }
}
