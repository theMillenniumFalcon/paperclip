"use client"

import { ChartAreaInteractive } from "@/components/chart-area-interactive"
import { DataTable } from "@/components/data-table"
import { useDashboard } from "@/components/dashboard-context"
import { SectionCards } from "@/components/section-cards"
import { DatabaseView } from "@/components/sections/database-view"
import { EvalsView } from "@/components/sections/evals-view"
import { MemoryView } from "@/components/sections/memory-view"
import { SettingsView } from "@/components/sections/settings-view"
import { SpendView } from "@/components/sections/spend-view"
import { ToolsView } from "@/components/sections/tools-view"
import { API_BASE } from "@/lib/api"

function Offline({ message }: { message: string }) {
  return (
    <div className="mx-4 rounded-xl border p-6 lg:mx-6">
      <h2 className="text-base font-medium">Paperclip API is not reachable</h2>
      <p className="mt-2 text-sm text-muted-foreground">{message}</p>
      <p className="mt-3 text-sm">
        Start <code className="rounded bg-muted px-1.5 py-0.5">paperclip api</code> and
        open this app on an allowlisted origin. Requests go to{" "}
        <code className="rounded bg-muted px-1.5 py-0.5">{API_BASE}</code>.
      </p>
    </div>
  )
}

export function Cockpit() {
  const { section, data, error, loading } = useDashboard()

  if (!data) {
    if (loading) {
      return <p className="px-4 text-sm text-muted-foreground lg:px-6">Loading the Paperclip API…</p>
    }
    return <Offline message={error || "The request failed."} />
  }

  if (section === "overview") {
    return (
      <div className="flex flex-col gap-4 md:gap-6">
        <SectionCards />
        <div className="px-4 lg:px-6">
          <ChartAreaInteractive />
        </div>
        <DataTable />
      </div>
    )
  }
  if (section === "turns") return <DataTable />
  if (section === "memory") return <MemoryView />
  if (section === "tools") return <ToolsView />
  if (section === "database") return <DatabaseView />
  if (section === "evals") return <EvalsView />
  if (section === "spend") return <SpendView />
  return <SettingsView />
}
