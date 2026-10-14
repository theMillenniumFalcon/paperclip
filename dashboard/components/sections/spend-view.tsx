"use client"

import { useDashboard } from "@/components/dashboard-context"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { formatCost, formatTokens } from "@/lib/format"

export function SpendView() {
  const { data } = useDashboard()
  if (!data) return null
  const usage = data.usage

  return (
    <div className="grid gap-4 px-4 lg:px-6">
      <div className="grid gap-4 @xl/main:grid-cols-3">
        <Card>
          <CardHeader>
            <CardDescription>All-time cost (est.)</CardDescription>
            <CardTitle>{formatCost(usage.total_cost)}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">{usage.calls} calls on the ledger</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Input tokens</CardDescription>
            <CardTitle>{formatTokens(usage.total_in)}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Output tokens</CardDescription>
            <CardTitle>{formatTokens(usage.total_out)}</CardTitle>
          </CardHeader>
        </Card>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>By provider</CardTitle>
          <CardDescription>Dollars are approximate and labelled as an estimate.</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Provider</TableHead>
                <TableHead>Calls</TableHead>
                <TableHead>In</TableHead>
                <TableHead>Out</TableHead>
                <TableHead className="text-right">Cost est.</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {usage.by_provider.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground">
                    usage.jsonl is empty.
                  </TableCell>
                </TableRow>
              ) : (
                usage.by_provider.map((row) => (
                  <TableRow key={row.provider}>
                    <TableCell>{row.provider}</TableCell>
                    <TableCell>{row.calls}</TableCell>
                    <TableCell>{formatTokens(row.in)}</TableCell>
                    <TableCell>{formatTokens(row.out)}</TableCell>
                    <TableCell className="text-right">{formatCost(row.cost)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>By day</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Calls</TableHead>
                <TableHead>In</TableHead>
                <TableHead>Out</TableHead>
                <TableHead className="text-right">Cost est.</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {usage.by_day.map((row) => (
                <TableRow key={row.date}>
                  <TableCell>{row.date}</TableCell>
                  <TableCell>{row.calls}</TableCell>
                  <TableCell>{formatTokens(row.in)}</TableCell>
                  <TableCell>{formatTokens(row.out)}</TableCell>
                  <TableCell className="text-right">{formatCost(row.cost)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
