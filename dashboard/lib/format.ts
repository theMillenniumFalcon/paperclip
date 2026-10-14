export function formatTokens(n: number): string {
  if (!Number.isFinite(n)) return "0"
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`
  if (Math.abs(n) >= 1_000) return `${(n / 1_000).toFixed(1)}k`
  return String(Math.round(n))
}

export function formatCost(n: number): string {
  if (!Number.isFinite(n)) return "$0.00"
  if (n > 0 && n < 0.01) return `$${n.toFixed(4)}`
  return `$${n.toFixed(2)}`
}

export function formatMs(n: number | null | undefined): string {
  if (n == null || !Number.isFinite(n)) return "—"
  if (n >= 1000) return `${(n / 1000).toFixed(1)}s`
  return `${Math.round(n)}ms`
}

export function formatBytes(n: number): string {
  if (!Number.isFinite(n) || n <= 0) return "0 B"
  if (n >= 1_048_576) return `${(n / 1_048_576).toFixed(1)} MB`
  if (n >= 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${n} B`
}

export function formatWhen(ts?: string | null): string {
  if (!ts) return "—"
  const date = new Date(ts)
  if (Number.isNaN(date.getTime())) return ts.replace("T", " ").slice(0, 19)
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export function dayKey(ts?: string | null): string {
  if (!ts) return ""
  return ts.slice(0, 10)
}
