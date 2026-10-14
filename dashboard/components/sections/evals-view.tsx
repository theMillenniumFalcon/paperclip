"use client"

import { useDashboard } from "@/components/dashboard-context"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { formatWhen } from "@/lib/format"
import type { EvalReport } from "@/lib/types"

function verdictVariant(value?: string) {
  if (value === "pass") return "secondary" as const
  if (value === "fail") return "destructive" as const
  return "outline" as const
}

function SuiteLine({ report }: { report: EvalReport }) {
  const suites = report.suites ?? {}
  const text = Object.entries(suites)
    .map(([name, counts]) => `${name} ${counts.passed ?? 0} passed / ${counts.failed ?? 0} failed`)
    .join(" · ")
  return <span>{text || "—"}</span>
}

export function EvalsView() {
  const { data } = useDashboard()
  if (!data) return null
  const report = data.eval_report

  return (
    <div className="grid gap-4 px-4 lg:px-6">
      <div className="grid gap-4 @xl/main:grid-cols-2">
        <Card>
          <CardHeader>
            <CardDescription>Deterministic</CardDescription>
            <CardTitle className="flex items-center gap-2">
              <Badge variant={verdictVariant(report?.deterministic)}>
                {report?.deterministic ?? "no report"}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {report ? <SuiteLine report={report} /> : "Run the release gate to write eval_report.json."}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Judge</CardDescription>
            <CardTitle>
              <Badge variant={verdictVariant(report?.judge)}>{report?.judge ?? "no report"}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {report?.ran_at ? `Last run ${formatWhen(report.ran_at)}` : "No timestamp yet."}
          </CardContent>
        </Card>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>History</CardTitle>
          <CardDescription>Last lines of eval_runs.jsonl, newest first.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-hidden rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>When</TableHead>
                  <TableHead>Deterministic</TableHead>
                  <TableHead>Judge</TableHead>
                  <TableHead>Suites</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.eval_history.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="h-20 text-center text-muted-foreground">
                      No eval runs recorded.
                    </TableCell>
                  </TableRow>
                ) : (
                  data.eval_history.map((row, index) => (
                    <TableRow key={`${row.ran_at}-${index}`}>
                      <TableCell>{formatWhen(row.ran_at)}</TableCell>
                      <TableCell>
                        <Badge variant={verdictVariant(row.deterministic)}>{row.deterministic}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={verdictVariant(row.judge)}>{row.judge}</Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        <SuiteLine report={row} />
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
