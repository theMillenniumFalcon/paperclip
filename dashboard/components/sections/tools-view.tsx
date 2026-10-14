"use client"

import { useDashboard } from "@/components/dashboard-context"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export function ToolsView() {
  const { data } = useDashboard()
  if (!data) return null
  const groups = new Map<string, typeof data.tools.catalog>()
  for (const tool of data.tools.catalog) {
    const list = groups.get(tool.source) ?? []
    list.push(tool)
    groups.set(tool.source, list)
  }

  return (
    <div className="grid gap-4 px-4 lg:px-6">
      <div className="flex flex-wrap gap-2">
        <Badge variant={data.tools.mcp.configured ? "secondary" : "outline"}>
          MCP {data.tools.mcp.configured ? data.tools.mcp.servers.join(", ") || "configured" : "not configured"}
        </Badge>
        <Badge variant="outline">{data.tools.mcp.live ? "MCP live" : "MCP display catalog"}</Badge>
        <Badge variant="outline">Apple tools {data.tools.apple_on ? "on" : "off"}</Badge>
      </div>
      {[...groups.entries()].map(([source, tools]) => (
        <Card key={source}>
          <CardHeader>
            <CardTitle className="capitalize">{source}</CardTitle>
            <CardDescription>{tools.length} available</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3">
            {tools.map((tool) => (
              <div key={tool.name}>
                <div className="font-medium">{tool.name}</div>
                <p className="text-sm text-muted-foreground">{tool.description}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      ))}
      <Card>
        <CardHeader>
          <CardTitle>Coming soon</CardTitle>
          <CardDescription>Planned capabilities that are not wired in.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3">
          {data.tools.planned.map((tool) => (
            <div key={tool.name}>
              <div className="flex items-center gap-2">
                <span className="font-medium">{tool.name}</span>
                <Badge variant="outline">{tool.box}</Badge>
              </div>
              <p className="text-sm text-muted-foreground">{tool.description}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
