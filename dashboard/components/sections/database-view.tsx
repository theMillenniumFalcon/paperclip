"use client"

import * as React from "react"
import { toast } from "sonner"

import { useDashboard } from "@/components/dashboard-context"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { postJson } from "@/lib/api"
import { formatBytes } from "@/lib/format"

const fieldClass =
  "border-input bg-transparent min-h-24 w-full rounded-lg border px-3 py-2 font-mono text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"

export function DatabaseView() {
  const { data } = useDashboard()
  const [sql, setSql] = React.useState("SELECT * FROM facts ORDER BY id DESC LIMIT 20")
  const [result, setResult] = React.useState<{ columns: string[]; rows: string[][] } | null>(null)
  const [busy, setBusy] = React.useState(false)

  if (!data) return null

  async function runQuery() {
    setBusy(true)
    try {
      const out = await postJson<{ columns?: string[]; rows?: string[][]; error?: string }>(
        "/api/query",
        { sql },
      )
      if (out.error) {
        toast.error(out.error)
        setResult(null)
      } else {
        setResult({ columns: out.columns ?? [], rows: out.rows ?? [] })
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Query failed")
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="grid gap-4 px-4 lg:px-6">
      <Card>
        <CardHeader>
          <CardTitle>state.db</CardTitle>
          <CardDescription>
            {data.db.path} · {formatBytes(data.db.size)}
            {data.db.fts.length ? ` · FTS ${data.db.fts.join(", ")}` : ""}
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Tables: {data.db.all_tables.join(", ") || "none"}
        </CardContent>
      </Card>
      <Tabs defaultValue={data.db.tables[0]?.name ?? "query"}>
        <TabsList className="flex h-auto flex-wrap">
          {data.db.tables.map((table) => (
            <TabsTrigger key={table.name} value={table.name}>
              {table.name} ({table.count})
            </TabsTrigger>
          ))}
        </TabsList>
        {data.db.tables.map((table) => (
          <TabsContent key={table.name} value={table.name}>
            <div className="overflow-auto rounded-lg border">
              <Table>
                <TableHeader className="bg-muted/40">
                  <TableRow>
                    {table.columns.map((column) => (
                      <TableHead key={column}>
                        {column}
                        <span className="ml-1 font-normal text-muted-foreground">
                          {table.types[column]}
                        </span>
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {table.sample.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={Math.max(table.columns.length, 1)} className="h-20 text-center">
                        Empty table
                      </TableCell>
                    </TableRow>
                  ) : (
                    table.sample.map((row, index) => (
                      <TableRow key={index}>
                        {table.columns.map((column) => (
                          <TableCell key={column} className="max-w-[240px] truncate">
                            {row[column] == null ? "" : String(row[column])}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </TabsContent>
        ))}
      </Tabs>
      <Card>
        <CardHeader>
          <CardTitle>Read-only SQL</CardTitle>
          <CardDescription>One SELECT or WITH statement, capped at 200 rows.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3">
          <textarea className={fieldClass} value={sql} onChange={(event) => setSql(event.target.value)} />
          <Button className="w-fit" disabled={busy} onClick={() => void runQuery()}>
            {busy ? "Running…" : "Run query"}
          </Button>
          {result ? (
            <div className="overflow-auto rounded-lg border">
              <Table>
                <TableHeader>
                  <TableRow>
                    {result.columns.map((column) => (
                      <TableHead key={column}>{column}</TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {result.rows.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={Math.max(result.columns.length, 1)} className="text-center">
                        No rows
                      </TableCell>
                    </TableRow>
                  ) : (
                    result.rows.map((row, index) => (
                      <TableRow key={index}>
                        {row.map((cell, cellIndex) => (
                          <TableCell key={cellIndex} className="max-w-[240px] truncate">
                            {cell}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  )
}
