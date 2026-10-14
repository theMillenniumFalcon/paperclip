"use client"

import * as React from "react"
import { toast } from "sonner"

import { useDashboard } from "@/components/dashboard-context"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { postJson } from "@/lib/api"
import { formatWhen } from "@/lib/format"
import type { Fact } from "@/lib/types"

const fieldClass =
  "border-input bg-transparent min-h-28 w-full rounded-lg border px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"

function skillSource(skill: { name: string; description: string; body: string }) {
  return `---\nname: ${skill.name}\ndescription: ${skill.description}\n---\n${skill.body}`
}

export function MemoryView() {
  const { data, refresh } = useDashboard()
  const [soulDraft, setSoulDraft] = React.useState<string | null>(null)
  const [skillPath, setSkillPath] = React.useState<string | null>(null)
  const [skillDraft, setSkillDraft] = React.useState<string | null>(null)
  const [editing, setEditing] = React.useState<Fact | null>(null)
  const soul = soulDraft ?? data?.soul ?? ""
  const selected =
    data?.skills.find((skill) => skill.path === skillPath) ?? data?.skills[0]
  const skillText = skillDraft ?? (selected ? skillSource(selected) : "")

  async function act(body: Record<string, unknown>, ok: string) {
    const result = await postJson<{ ok?: boolean; error?: string }>("/api/memory", body)
    if (result.error) toast.error(result.error)
    else {
      toast.success(ok)
      await refresh()
    }
  }

  if (!data) return null

  return (
    <Tabs defaultValue="facts" className="px-4 lg:px-6">
      <TabsList className="flex h-auto flex-wrap">
        <TabsTrigger value="facts">Facts</TabsTrigger>
        <TabsTrigger value="episodes">Episodes</TabsTrigger>
        <TabsTrigger value="soul">Soul</TabsTrigger>
        <TabsTrigger value="skills">Skills</TabsTrigger>
        <TabsTrigger value="inbox">Inbox</TabsTrigger>
        <TabsTrigger value="calendar">Calendar</TabsTrigger>
        <TabsTrigger value="outbox">Outbox</TabsTrigger>
      </TabsList>
      <TabsContent value="facts" className="grid gap-3">
        <p className="text-sm text-muted-foreground">
          {data.chat_pending} chat rows waiting to consolidate (every {data.consolidate_every}).
        </p>
        {editing ? (
          <Card>
            <CardHeader>
              <CardTitle>Edit fact #{editing.id}</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-2">
              <Input
                value={editing.subject ?? ""}
                onChange={(event) => setEditing({ ...editing, subject: event.target.value })}
                placeholder="Subject"
              />
              <textarea
                className={fieldClass}
                value={editing.content}
                onChange={(event) => setEditing({ ...editing, content: event.target.value })}
              />
              <div className="flex gap-2">
                <Button
                  onClick={() =>
                    void act(
                      {
                        action: "update_fact",
                        id: editing.id,
                        content: editing.content,
                        subject: editing.subject,
                      },
                      "Fact updated",
                    ).then(() => setEditing(null))
                  }
                >
                  Save
                </Button>
                <Button variant="outline" onClick={() => setEditing(null)}>
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : null}
        <div className="grid gap-2">
          {data.facts.length === 0 ? (
            <p className="text-sm text-muted-foreground">No facts stored.</p>
          ) : (
            data.facts.map((fact) => (
              <Card key={fact.id}>
                <CardHeader>
                  <CardTitle className="text-base">{fact.subject || `Fact ${fact.id}`}</CardTitle>
                  <CardDescription>
                    {fact.source || "unknown"} · {formatWhen(fact.created_at)}
                  </CardDescription>
                </CardHeader>
                <CardContent className="grid gap-3">
                  <p className="whitespace-pre-wrap text-sm">{fact.content}</p>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => setEditing(fact)}>
                      Edit
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => void act({ action: "delete_fact", id: fact.id }, "Fact deleted")}
                    >
                      Delete
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </TabsContent>
      <TabsContent value="episodes" className="grid gap-2">
        {data.episodes.length === 0 ? (
          <p className="text-sm text-muted-foreground">No episodes stored.</p>
        ) : (
          data.episodes.map((episode) => (
            <Card key={episode.id}>
              <CardHeader>
                <CardTitle className="text-base">{formatWhen(episode.happened_at)}</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-3">
                <p className="text-sm whitespace-pre-wrap">{episode.summary}</p>
                <Button
                  size="sm"
                  variant="destructive"
                  className="w-fit"
                  onClick={() =>
                    void act({ action: "delete_episode", id: episode.id }, "Episode deleted")
                  }
                >
                  Delete
                </Button>
              </CardContent>
            </Card>
          ))
        )}
      </TabsContent>
      <TabsContent value="soul">
        <Card>
          <CardHeader>
            <CardTitle>SOUL.md</CardTitle>
            <CardDescription>Rewrites the file the next turn will read.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3">
            <textarea className={`${fieldClass} min-h-64 font-mono`} value={soul} onChange={(event) => setSoulDraft(event.target.value)} />
            <Button
              className="w-fit"
              onClick={() => void act({ action: "save_soul", content: soul }, "SOUL.md saved")}
            >
              Save soul
            </Button>
          </CardContent>
        </Card>
      </TabsContent>
      <TabsContent value="skills" className="grid gap-3">
        <div className="flex flex-wrap gap-2">
          {data.skills.map((skill) => (
            <Button
              key={skill.path}
              size="sm"
              variant={skill.path === selected?.path ? "default" : "outline"}
              onClick={() => {
                setSkillPath(skill.path)
                setSkillDraft(null)
              }}
            >
              {skill.name}
            </Button>
          ))}
        </div>
        {data.skills.length === 0 ? (
          <p className="text-sm text-muted-foreground">No skills loaded.</p>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>{selected?.name}</CardTitle>
              <CardDescription>{selected?.path}</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3">
              <textarea
                className={`${fieldClass} min-h-64 font-mono`}
                value={skillText}
                onChange={(event) => setSkillDraft(event.target.value)}
              />
              <Button
                className="w-fit"
                onClick={() =>
                  void act({ action: "save_skill", path: selected?.path, content: skillText }, "Skill saved")
                }
              >
                Save skill
              </Button>
            </CardContent>
          </Card>
        )}
      </TabsContent>
      <TabsContent value="inbox" className="grid gap-2">
        {data.chat_log.length === 0 ? (
          <p className="text-sm text-muted-foreground">Chat log is empty.</p>
        ) : (
          data.chat_log.map((row, index) => (
            <div key={`${row.created_at}-${index}`} className="rounded-lg border p-3 text-sm">
              <div className="mb-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                <Badge variant="outline">{row.role}</Badge>
                <span>{row.source || "unknown"}</span>
                <span>{row.session_id}</span>
                <span>{formatWhen(row.created_at)}</span>
                {row.consolidated ? <Badge variant="secondary">consolidated</Badge> : null}
              </div>
              <p className="whitespace-pre-wrap">{row.content}</p>
            </div>
          ))
        )}
      </TabsContent>
      <TabsContent value="calendar" className="grid gap-2">
        {data.calendar.length === 0 ? (
          <p className="text-sm text-muted-foreground">No local calendar events.</p>
        ) : (
          data.calendar.map((event, index) => (
            <Card key={`${event.start}-${index}`}>
              <CardHeader>
                <CardTitle className="text-base">{event.title || "Untitled"}</CardTitle>
                <CardDescription>
                  {formatWhen(event.start)} – {formatWhen(event.end)}
                </CardDescription>
              </CardHeader>
              {event.attendees ? (
                <CardContent className="text-sm text-muted-foreground">{event.attendees}</CardContent>
              ) : null}
            </Card>
          ))
        )}
      </TabsContent>
      <TabsContent value="outbox" className="grid gap-2">
        {data.outbox.length === 0 ? (
          <p className="text-sm text-muted-foreground">Outbox is empty.</p>
        ) : (
          data.outbox.map((note) => (
            <Card key={note.name}>
              <CardHeader>
                <CardTitle className="text-base">{note.name}</CardTitle>
              </CardHeader>
              <CardContent className="text-sm whitespace-pre-wrap">{note.text}</CardContent>
            </Card>
          ))
        )}
      </TabsContent>
    </Tabs>
  )
}
