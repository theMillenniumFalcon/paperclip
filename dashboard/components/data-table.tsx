"use client"

import * as React from "react"

import { useDashboard } from "@/components/dashboard-context"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { formatCost, formatMs, formatWhen } from "@/lib/format"
import type { Turn } from "@/lib/types"

function statusVariant(status?: string) {
  if (status === "error") return "destructive" as const
  if (status === "warn") return "outline" as const
  return "secondary" as const
}

function TurnBody({ turn }: { turn: Turn }) {
  return (
    <div className="grid gap-3 px-2 py-3 text-sm">
      <div>
        <div className="text-xs text-muted-foreground">Reply</div>
        <p className="whitespace-pre-wrap">{turn.reply || "—"}</p>
      </div>
      {turn.tools?.length ? (
        <div className="grid gap-2">
          {turn.tools.map((tool, index) => (
            <div key={`${tool.tool}-${index}`} className="rounded-lg border p-2">
              <div className="flex items-center gap-2">
                <span className="font-medium">{tool.tool}</span>
                <Badge variant={statusVariant(tool.status)}>{tool.status || "ok"}</Badge>
              </div>
              <p className="mt-1 text-muted-foreground">{tool.summary || tool.output}</p>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  )
}

export function DataTable() {
  const { data } = useDashboard()
  const [query, setQuery] = React.useState("")
  const [open, setOpen] = React.useState<number | null>(null)
  const turns = data?.turns ?? []
  const filtered = turns.filter((turn) =>
    (turn.user_message || "").toLowerCase().includes(query.trim().toLowerCase()),
  )

  return (
    <Tabs defaultValue="turns" className="w-full gap-4">
      <div className="flex flex-col gap-3 px-4 lg:px-6 sm:flex-row sm:items-center sm:justify-between">
        <TabsList>
          <TabsTrigger value="turns">Recent turns</TabsTrigger>
          <TabsTrigger value="traces">Trace tail</TabsTrigger>
        </TabsList>
        <Input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Filter turns"
          className="sm:max-w-xs"
        />
      </div>
      <TabsContent value="turns" className="px-4 lg:px-6">
        <div className="overflow-hidden rounded-lg border">
          <Table>
            <TableHeader className="bg-muted/40">
              <TableRow>
                <TableHead>When</TableHead>
                <TableHead>Message</TableHead>
                <TableHead>Gate</TableHead>
                <TableHead>Tools</TableHead>
                <TableHead>Latency</TableHead>
                <TableHead className="text-right">Cost est.</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                    No turns yet. Open chat and send a message.
                  </TableCell>
                </TableRow>
              ) : (
                filtered.map((turn, index) => {
                  const errors = turn.tools?.filter((tool) => tool.status === "error").length ?? 0
                  return (
                    <React.Fragment key={`${turn.ts}-${index}`}>
                      <TableRow
                        className="cursor-pointer"
                        onClick={() => setOpen(open === index ? null : index)}
                      >
                        <TableCell className="whitespace-nowrap text-muted-foreground">
                          {formatWhen(turn.ts)}
                        </TableCell>
                        <TableCell className="max-w-[280px] truncate font-medium">
                          {turn.unfinished ? "Unfinished · " : ""}
                          {turn.user_message || "(empty)"}
                        </TableCell>
                        <TableCell>
                          {turn.gate?.decision ? (
                            <Badge variant="outline">{turn.gate.decision}</Badge>
                          ) : (
                            "—"
                          )}
                        </TableCell>
                        <TableCell>
                          <span className="tabular-nums">{turn.tools?.length ?? 0}</span>
                          {errors > 0 ? (
                            <Badge variant="destructive" className="ml-2">
                              {errors} error
                            </Badge>
                          ) : null}
                        </TableCell>
                        <TableCell className="tabular-nums">{formatMs(turn.latency_ms)}</TableCell>
                        <TableCell className="text-right tabular-nums">
                          {formatCost(turn.cost ?? 0)}
                        </TableCell>
                      </TableRow>
                      {open === index ? (
                        <TableRow>
                          <TableCell colSpan={6}>
                            <TurnBody turn={turn} />
                          </TableCell>
                        </TableRow>
                      ) : null}
                    </React.Fragment>
                  )
                })
              )}
            </TableBody>
          </Table>
        </div>
      </TabsContent>
      <TabsContent value="traces" className="px-4 lg:px-6">
        <div className="overflow-hidden rounded-lg border">
          <Table>
            <TableHeader className="bg-muted/40">
              <TableRow>
                <TableHead>When</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Detail</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(data?.trace_tail ?? []).length === 0 ? (
                <TableRow>
                  <TableCell colSpan={3} className="h-24 text-center text-muted-foreground">
                    No trace lines yet{data?.trace_file ? "" : ""}.
                  </TableCell>
                </TableRow>
              ) : (
                data?.trace_tail.map((line, index) => (
                  <TableRow key={`${line.ts}-${index}`}>
                    <TableCell className="whitespace-nowrap text-muted-foreground">
                      {formatWhen(line.ts)}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{line.type || "event"}</Badge>
                    </TableCell>
                    <TableCell className="max-w-[420px] truncate">{line.detail}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
        {data?.trace_file ? (
          <p className="mt-2 text-xs text-muted-foreground">Latest file {data.trace_file}</p>
        ) : null}
      </TabsContent>
    </Tabs>
  )
}
