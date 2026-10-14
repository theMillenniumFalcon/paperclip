export type ToolStatus = "ok" | "warn" | "error" | string

export type GateEvent = {
  decision?: string
  reason?: string
  type?: string
  ts?: string
}

export type ToolEvent = {
  tool?: string
  args?: unknown
  output?: string
  status?: ToolStatus
  summary?: string
  type?: string
  ts?: string
}

export type LlmEvent = {
  ts?: string
  usage?: { in?: number; out?: number }
  iteration?: number
  stop_reason?: string
}

export type Turn = {
  user_message?: string
  ts?: string
  gate?: GateEvent | null
  llm_calls?: LlmEvent[]
  tools?: ToolEvent[]
  reply?: string | null
  iterations?: number
  unfinished?: boolean
  latency_ms?: number | null
  cost?: number
  consolidation?: { new_facts?: number }
}

export type UsageBucket = {
  date?: string
  provider?: string
  calls: number
  in: number
  out: number
  cost: number
}

export type Fact = {
  id: number
  subject?: string | null
  content: string
  source?: string | null
  created_at?: string
}

export type Episode = {
  id: number
  happened_at?: string
  summary: string
}

export type Skill = {
  name: string
  description: string
  body: string
  path: string
  rel?: string
  editable?: boolean
}

export type ToolCatalogItem = {
  name: string
  description: string
  source: string
}

export type PlannedTool = {
  name: string
  box: string
  description: string
}

export type DbTable = {
  name: string
  columns: string[]
  types: Record<string, string>
  count: number
  sample: Record<string, unknown>[]
}

export type EvalReport = {
  deterministic?: string
  judge?: string
  suites?: Record<string, { passed?: number; failed?: number }>
  ran_at?: string
}

export type ProviderSetting = {
  name: string
  key_env: string
  key_set: boolean
  key_last4: string
  default_model: string
}

export type DashboardData = {
  generated_at: string
  home: string
  provider: string
  model: string
  stats: {
    turns: number
    tool_calls: number
    tool_errors: number
    gate_skips: number
    gate_retrieves: number
    tokens_in: number
    tokens_out: number
    cost: number
    latency_avg: number
    latency_p95: number
    trace_files: number
  }
  turns: Turn[]
  wake_scans: Record<string, unknown>[]
  trace_tail: { type?: string; ts?: string; detail?: string }[]
  trace_file?: string | null
  facts: Fact[]
  episodes: Episode[]
  soul: string
  chat_pending: number
  chat_log: {
    role: string
    content: string
    consolidated?: number
    source?: string
    session_id?: string
    created_at?: string
  }[]
  sessions: {
    id: string
    title: string
    last: string
    sources: string[]
    messages: number
    last_at?: string
  }[]
  current_session: string
  consolidate_every: number
  calendar: {
    title?: string
    start?: string
    end?: string
    attendees?: string
    created_at?: string
  }[]
  outbox: { name: string; text: string }[]
  skills: Skill[]
  eval_report: EvalReport | null
  eval_history: EvalReport[]
  db: {
    path: string
    size: number
    tables: DbTable[]
    fts: string[]
    all_tables: string[]
  }
  settings: {
    provider: string
    model: string
    small_model: string
    providers: ProviderSetting[]
    search_key_env: string
    search_key_set: boolean
    search_key_last4: string
  }
  tools: {
    catalog: ToolCatalogItem[]
    mcp: { configured: boolean; servers: string[]; live: boolean }
    apple_on: boolean
    planned: PlannedTool[]
  }
  usage: {
    calls: number
    total_in: number
    total_out: number
    total_cost: number
    by_day: UsageBucket[]
    by_provider: UsageBucket[]
  }
}

export type Section =
  | "overview"
  | "turns"
  | "memory"
  | "tools"
  | "database"
  | "evals"
  | "spend"
  | "settings"

export const SECTION_LABEL: Record<Section, string> = {
  overview: "Overview",
  turns: "Turns",
  memory: "Memory",
  tools: "Tools",
  database: "Database",
  evals: "Evals",
  spend: "Spend",
  settings: "Settings",
}
