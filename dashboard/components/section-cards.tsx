"use client"

import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardAction,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { useDashboard } from "@/components/dashboard-context"
import { formatCost, formatMs, formatTokens } from "@/lib/format"
import { TrendingUpIcon, TriangleAlertIcon } from "lucide-react"

export function SectionCards() {
  const { data } = useDashboard()
  const stats = data?.stats
  const usage = data?.usage
  const turns = stats?.turns ?? 0
  const errors = stats?.tool_errors ?? 0

  return (
    <div className="grid grid-cols-1 gap-4 px-4 *:data-[slot=card]:bg-linear-to-t *:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card *:data-[slot=card]:shadow-xs lg:px-6 @xl/main:grid-cols-2 @5xl/main:grid-cols-4 dark:*:data-[slot=card]:bg-card">
      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Turns</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {turns.toLocaleString()}
          </CardTitle>
          <CardAction>
            <Badge variant="outline">
              <TrendingUpIcon />
              {stats?.trace_files ?? 0} files
            </Badge>
          </CardAction>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            {stats?.tool_calls ?? 0} tool calls
          </div>
          <div className="text-muted-foreground">
            Gate skipped {stats?.gate_skips ?? 0}, retrieved {stats?.gate_retrieves ?? 0}
          </div>
        </CardFooter>
      </Card>
      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Tool errors</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {errors.toLocaleString()}
          </CardTitle>
          <CardAction>
            <Badge variant={errors > 0 ? "destructive" : "outline"}>
              {errors > 0 ? <TriangleAlertIcon /> : <TrendingUpIcon />}
              {errors > 0 ? "needs a look" : "clean"}
            </Badge>
          </CardAction>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            From tool output text
          </div>
          <div className="text-muted-foreground">
            failed, error, or timed out
          </div>
        </CardFooter>
      </Card>
      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Latency p95</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {formatMs(stats?.latency_p95)}
          </CardTitle>
          <CardAction>
            <Badge variant="outline">avg {formatMs(stats?.latency_avg)}</Badge>
          </CardAction>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            {formatTokens(stats?.tokens_in ?? 0)} in · {formatTokens(stats?.tokens_out ?? 0)} out
          </div>
          <div className="text-muted-foreground">Tokens counted from traces</div>
        </CardFooter>
      </Card>
      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Spend (est.)</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {formatCost(usage?.total_cost ?? stats?.cost ?? 0)}
          </CardTitle>
          <CardAction>
            <Badge variant="outline">all-time</Badge>
          </CardAction>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            {usage?.calls ?? 0} ledger calls
          </div>
          <div className="text-muted-foreground">
            Trace window {formatCost(stats?.cost ?? 0)} · approximate
          </div>
        </CardFooter>
      </Card>
    </div>
  )
}
