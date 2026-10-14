import type { DashboardData } from "@/lib/types"

export const API_BASE = (
  process.env.NEXT_PUBLIC_PAPERCLIP_API || "http://127.0.0.1:7777"
).replace(/\/$/, "")

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof Blob ? {} : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
  })
  const text = await res.text()
  const data = text ? (JSON.parse(text) as T) : ({} as T)
  if (!res.ok) {
    const message =
      typeof data === "object" && data && "error" in data
        ? String((data as { error?: string }).error)
        : `Request failed (${res.status})`
    throw new Error(message)
  }
  return data
}

export function fetchDashboard(): Promise<DashboardData> {
  return request<DashboardData>("/api/data")
}

export function postJson<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: "POST", body: JSON.stringify(body) })
}

export function revealPath(path: string) {
  return request<{ ok?: boolean; error?: string; opened_in?: string; path?: string; revealed?: string }>(
    `/api/reveal?path=${encodeURIComponent(path)}`,
  )
}

export type StreamEvent = { kind: string; [key: string]: unknown }

export async function streamChat(
  message: string,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  })
  if (!res.ok || !res.body) {
    throw new Error(`Chat stream failed (${res.status})`)
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const chunks = buffer.split("\n\n")
    buffer = chunks.pop() ?? ""
    for (const chunk of chunks) {
      const line = chunk.split("\n").find((row) => row.startsWith("data: "))
      if (!line) continue
      onEvent(JSON.parse(line.slice(6)) as StreamEvent)
    }
  }
}

export function transcribe(wav: Blob) {
  return request<{ text?: string; error?: string }>("/api/voice", {
    method: "POST",
    body: wav,
    headers: { "Content-Type": "audio/wav" },
  })
}
