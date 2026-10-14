"use client"

import * as React from "react"
import { toast } from "sonner"

import { useDashboard } from "@/components/dashboard-context"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { postJson, streamChat, transcribe, type StreamEvent } from "@/lib/api"
import { startRecording } from "@/lib/wav"
import { MicIcon, SquareIcon } from "lucide-react"

type Line = {
  role: "user" | "assistant"
  content: string
  note?: string
}

export function ChatDock() {
  const { chatOpen, setChatOpen, data, refresh } = useDashboard()
  const [sessionId, setSessionId] = React.useState<string | null>(null)
  const [lines, setLines] = React.useState<Line[]>([])
  const [draft, setDraft] = React.useState("")
  const [busy, setBusy] = React.useState(false)
  const [recording, setRecording] = React.useState<null | { stop: () => Promise<Blob> }>(null)
  const scroller = React.useRef<HTMLDivElement>(null)
  const active = sessionId ?? data?.current_session ?? "default"

  const loadHistory = React.useCallback(async (id: string) => {
    const result = await postJson<{
      history?: { role: string; content: string }[]
      error?: string
      session_id?: string
    }>("/api/session", { action: "history", id })
    if (result.error) return
    setLines(
      (result.history ?? []).map((row) => ({
        role: row.role === "assistant" ? "assistant" : "user",
        content: row.content,
      })),
    )
  }, [])

  React.useEffect(() => {
    if (!chatOpen) return
    const id = window.setTimeout(() => {
      void loadHistory(active).catch(() => undefined)
    }, 0)
    return () => window.clearTimeout(id)
  }, [chatOpen, active, loadHistory])

  React.useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight })
  }, [lines])

  function onStream(event: StreamEvent) {
    if (event.kind === "text") {
      const delta = String(event.delta ?? "")
      setLines((current) => {
        const next = [...current]
        const last = next[next.length - 1]
        if (last?.role === "assistant") last.content += delta
        else next.push({ role: "assistant", content: delta })
        return next
      })
    } else if (event.kind === "gate") {
      const note = `gate ${String(event.decision ?? "")}`
      setLines((current) => {
        const next = [...current]
        const last = next[next.length - 1]
        if (last?.role === "assistant") last.note = note
        else next.push({ role: "assistant", content: "", note })
        return next
      })
    } else if (event.kind === "tool") {
      const note = `${String(event.tool ?? "tool")}`
      setLines((current) => {
        const next = [...current]
        const last = next[next.length - 1]
        if (last?.role === "assistant") last.note = [last.note, note].filter(Boolean).join(" · ")
        else next.push({ role: "assistant", content: "", note })
        return next
      })
    } else if (event.kind === "done") {
      if (event.error) toast.error(String(event.error))
      const reply = typeof event.reply === "string" ? event.reply : ""
      if (reply) {
        setLines((current) => {
          const next = [...current]
          const last = next[next.length - 1]
          if (last?.role === "assistant") last.content = reply
          else next.push({ role: "assistant", content: reply })
          return next
        })
      }
    }
  }

  async function send(text: string) {
    const message = text.trim()
    if (!message || busy) return
    setDraft("")
    setBusy(true)
    setLines((current) => [...current, { role: "user", content: message }, { role: "assistant", content: "" }])
    try {
      await streamChat(message, onStream)
      await refresh()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Chat failed")
    } finally {
      setBusy(false)
    }
  }

  async function newSession() {
    const result = await postJson<{ session_id?: string; error?: string }>("/api/session", {
      action: "new",
    })
    if (result.error || !result.session_id) {
      toast.error(result.error || "Could not start a session")
      return
    }
    setSessionId(result.session_id)
    setLines([])
  }

  async function switchSession(id: string) {
    const result = await postJson<{ error?: string }>("/api/session", { action: "switch", id })
    if (result.error) {
      toast.error(result.error)
      return
    }
    setSessionId(id)
  }

  async function toggleMic() {
    if (recording) {
      const blob = await recording.stop()
      setRecording(null)
      const result = await transcribe(blob)
      if (result.error) toast.error(result.error)
      else if (result.text) setDraft((current) => `${current} ${result.text}`.trim())
      return
    }
    try {
      const rec = await startRecording()
      setRecording(rec)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Microphone unavailable")
    }
  }

  return (
    <Sheet open={chatOpen} onOpenChange={setChatOpen}>
      <SheetContent side="right" className="w-full sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Chat</SheetTitle>
          <SheetDescription>Session {active}</SheetDescription>
        </SheetHeader>
        <div className="flex items-center gap-2 px-4">
          <Button size="sm" variant="outline" onClick={() => void newSession()}>
            New
          </Button>
          <select
            className="h-8 min-w-0 flex-1 rounded-lg border bg-transparent px-2 text-sm"
            value={active}
            onChange={(event) => void switchSession(event.target.value)}
          >
            {(data?.sessions ?? []).map((session) => (
              <option key={session.id} value={session.id}>
                {session.title}
              </option>
            ))}
            {(data?.sessions ?? []).every((session) => session.id !== active) ? (
              <option value={active}>{active}</option>
            ) : null}
          </select>
        </div>
        <div ref={scroller} className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto px-4">
          {lines.length === 0 ? (
            <p className="text-sm text-muted-foreground">Send a message to run one dashboard turn.</p>
          ) : (
            lines.map((line, index) => (
              <div
                key={index}
                className={
                  line.role === "user"
                    ? "ml-8 rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground"
                    : "mr-8 rounded-lg border px-3 py-2 text-sm"
                }
              >
                {line.note ? (
                  <Badge variant="outline" className="mb-1">
                    {line.note}
                  </Badge>
                ) : null}
                <p className="whitespace-pre-wrap">{line.content || (busy ? "…" : "")}</p>
              </div>
            ))
          )}
        </div>
        <form
          className="mt-auto flex gap-2 border-t p-4"
          onSubmit={(event) => {
            event.preventDefault()
            void send(draft)
          }}
        >
          <Input
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Message Paperclip"
            disabled={busy}
          />
          <Button
            type="button"
            size="icon"
            variant={recording ? "destructive" : "outline"}
            onClick={() => void toggleMic()}
            disabled={busy}
          >
            {recording ? <SquareIcon /> : <MicIcon />}
            <span className="sr-only">{recording ? "Stop recording" : "Record"}</span>
          </Button>
          <Button type="submit" disabled={busy || !draft.trim()}>
            Send
          </Button>
        </form>
      </SheetContent>
    </Sheet>
  )
}
