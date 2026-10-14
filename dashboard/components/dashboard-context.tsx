"use client"

import * as React from "react"

import { fetchDashboard } from "@/lib/api"
import type { DashboardData, Section } from "@/lib/types"

type DashboardContextValue = {
  data: DashboardData | null
  error: string | null
  loading: boolean
  refresh: () => Promise<void>
  section: Section
  setSection: (section: Section) => void
  chatOpen: boolean
  setChatOpen: (open: boolean) => void
}

const DashboardContext = React.createContext<DashboardContextValue | null>(null)

export function DashboardProvider({ children }: { children: React.ReactNode }) {
  const [data, setData] = React.useState<DashboardData | null>(null)
  const [error, setError] = React.useState<string | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [section, setSection] = React.useState<Section>("overview")
  const [chatOpen, setChatOpen] = React.useState(false)

  const refresh = React.useCallback(async () => {
    try {
      const next = await fetchDashboard()
      setData(next)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reach the Paperclip API")
    } finally {
      setLoading(false)
    }
  }, [])

  React.useEffect(() => {
    const kick = window.setTimeout(() => void refresh(), 0)
    const id = window.setInterval(() => void refresh(), 5000)
    return () => {
      window.clearTimeout(kick)
      window.clearInterval(id)
    }
  }, [refresh])

  const value = React.useMemo(
    () => ({ data, error, loading, refresh, section, setSection, chatOpen, setChatOpen }),
    [data, error, loading, refresh, section, chatOpen],
  )

  return <DashboardContext.Provider value={value}>{children}</DashboardContext.Provider>
}

export function useDashboard() {
  const value = React.useContext(DashboardContext)
  if (!value) throw new Error("useDashboard must be used within DashboardProvider")
  return value
}
