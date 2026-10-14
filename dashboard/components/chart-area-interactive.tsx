"use client"

import * as React from "react"
import { Area, AreaChart, CartesianGrid, XAxis } from "recharts"

import { useDashboard } from "@/components/dashboard-context"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  ToggleGroup,
  ToggleGroupItem,
} from "@/components/ui/toggle-group"
export const description = "Token usage by day"

const chartConfig = {
  tokens: { label: "Tokens" },
  in: { label: "Input", color: "var(--chart-1)" },
  out: { label: "Output", color: "var(--chart-2)" },
} satisfies ChartConfig

export function ChartAreaInteractive() {
  const { data } = useDashboard()
  const [timeRange, setTimeRange] = React.useState("30d")

  const chartData = React.useMemo(() => {
    const days = [...(data?.usage.by_day ?? [])].reverse()
    return days.map((row) => ({
      date: row.date ?? "",
      in: row.in,
      out: row.out,
    }))
  }, [data])

  const filteredData = chartData.filter((item) => {
    if (!item.date || timeRange === "all") return true
    const days = timeRange === "7d" ? 7 : 30
    const start = new Date()
    start.setHours(0, 0, 0, 0)
    start.setDate(start.getDate() - (days - 1))
    const cutoff = start.toISOString().slice(0, 10)
    return item.date >= cutoff
  })

  const rangeLabel =
    timeRange === "7d" ? "Last 7 days" : timeRange === "all" ? "All ledger days" : "Last 30 days"

  return (
    <Card className="@container/card">
      <CardHeader>
        <CardTitle>Token usage</CardTitle>
        <CardDescription>
          <span className="hidden @[540px]/card:block">
            {rangeLabel} · estimated from usage.jsonl
          </span>
          <span className="@[540px]/card:hidden">{rangeLabel}</span>
        </CardDescription>
        <CardAction>
          <ToggleGroup
            multiple={false}
            value={timeRange ? [timeRange] : []}
            onValueChange={(value) => {
              setTimeRange(value[0] ?? "30d")
            }}
            variant="outline"
            className="hidden *:data-[slot=toggle-group-item]:px-4! @[767px]/card:flex"
          >
            <ToggleGroupItem value="all">All</ToggleGroupItem>
            <ToggleGroupItem value="30d">Last 30 days</ToggleGroupItem>
            <ToggleGroupItem value="7d">Last 7 days</ToggleGroupItem>
          </ToggleGroup>
          <Select
            value={timeRange}
            onValueChange={(value) => {
              if (value !== null) setTimeRange(value)
            }}
          >
            <SelectTrigger
              className="flex w-40 **:data-[slot=select-value]:block **:data-[slot=select-value]:truncate @[767px]/card:hidden"
              size="sm"
              aria-label="Select a range"
            >
              <SelectValue placeholder="Last 30 days" />
            </SelectTrigger>
            <SelectContent className="rounded-xl">
              <SelectItem value="all" className="rounded-lg">
                All ledger days
              </SelectItem>
              <SelectItem value="30d" className="rounded-lg">
                Last 30 days
              </SelectItem>
              <SelectItem value="7d" className="rounded-lg">
                Last 7 days
              </SelectItem>
            </SelectContent>
          </Select>
        </CardAction>
      </CardHeader>
      <CardContent className="px-2 pt-4 sm:px-6 sm:pt-6">
        {filteredData.length === 0 ? (
          <div className="flex h-[250px] items-center justify-center text-sm text-muted-foreground">
            No usage ledger rows in this range yet.
          </div>
        ) : (
          <ChartContainer config={chartConfig} className="aspect-auto h-[250px] w-full">
            <AreaChart data={filteredData}>
              <defs>
                <linearGradient id="fillIn" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--color-in)" stopOpacity={1} />
                  <stop offset="95%" stopColor="var(--color-in)" stopOpacity={0.1} />
                </linearGradient>
                <linearGradient id="fillOut" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--color-out)" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="var(--color-out)" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid vertical={false} />
              <XAxis
                dataKey="date"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                minTickGap={32}
                tickFormatter={(value) => {
                  const date = new Date(`${value}T12:00:00`)
                  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" })
                }}
              />
              <ChartTooltip
                cursor={false}
                content={
                  <ChartTooltipContent
                    labelFormatter={(value) =>
                      new Date(`${value}T12:00:00`).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                      })
                    }
                    indicator="dot"
                  />
                }
              />
              <Area dataKey="out" type="natural" fill="url(#fillOut)" stroke="var(--color-out)" stackId="a" />
              <Area dataKey="in" type="natural" fill="url(#fillIn)" stroke="var(--color-in)" stackId="a" />
            </AreaChart>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  )
}
