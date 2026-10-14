"use client"

import * as React from "react"
import { toast } from "sonner"

import { useDashboard } from "@/components/dashboard-context"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { postJson } from "@/lib/api"

export function SettingsView() {
  const { data, refresh } = useDashboard()
  const settings = data?.settings
  const [draft, setDraft] = React.useState<{
    provider: string
    model: string
    smallModel: string
  } | null>(null)
  const [keys, setKeys] = React.useState<Record<string, string>>({})
  const [searchKey, setSearchKey] = React.useState("")
  const [busy, setBusy] = React.useState(false)
  const provider = draft?.provider ?? settings?.provider ?? ""
  const model = draft?.model ?? settings?.model ?? ""
  const smallModel = draft?.smallModel ?? settings?.small_model ?? ""

  function updateDraft(patch: Partial<{ provider: string; model: string; smallModel: string }>) {
    setDraft({ provider, model, smallModel, ...patch })
  }

  if (!settings) return null

  async function save() {
    setBusy(true)
    const payloadKeys: Record<string, string> = {}
    for (const [name, value] of Object.entries(keys)) {
      if (value.trim()) payloadKeys[name] = value.trim()
    }
    if (searchKey.trim()) payloadKeys[settings!.search_key_env] = searchKey.trim()
    try {
      const result = await postJson<{ ok?: boolean; error?: string }>("/api/settings", {
        provider,
        model,
        small_model: smallModel,
        keys: payloadKeys,
      })
      if (result.error) toast.error(result.error)
      else {
        toast.success("Provider settings applied")
        setKeys({})
        setSearchKey("")
        await refresh()
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not save settings")
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="grid gap-4 px-4 lg:px-6">
      <Card>
        <CardHeader>
          <CardTitle>Provider</CardTitle>
          <CardDescription>
            Writes allowlisted keys to .env and rebuilds the shared agent. Blank key fields are left unchanged.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:max-w-lg">
          <div className="grid gap-2">
            <Label>Provider</Label>
            <Select
              value={provider}
              onValueChange={(value) => {
                if (!value) return
                updateDraft({
                  provider: value,
                  model: settings.providers.find((item) => item.name === value)?.default_model ?? model,
                })
              }}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {settings.providers.map((item) => (
                  <SelectItem key={item.name} value={item.name}>
                    {item.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="model">Model</Label>
            <Input id="model" value={model} onChange={(event) => updateDraft({ model: event.target.value })} />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="small-model">Small model</Label>
            <Input
              id="small-model"
              value={smallModel}
              onChange={(event) => updateDraft({ smallModel: event.target.value })}
            />
          </div>
          <Button className="w-fit" disabled={busy} onClick={() => void save()}>
            {busy ? "Saving…" : "Apply settings"}
          </Button>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>API keys</CardTitle>
          <CardDescription>Only the last four characters are shown. New values replace the stored key.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          {settings.providers.map((item) => (
            <div key={item.key_env} className="grid gap-2 sm:max-w-lg">
              <Label htmlFor={item.key_env} className="flex items-center gap-2">
                {item.key_env}
                <Badge variant={item.key_set ? "secondary" : "outline"}>
                  {item.key_set ? `set ····${item.key_last4}` : "missing"}
                </Badge>
              </Label>
              <Input
                id={item.key_env}
                type="password"
                autoComplete="off"
                placeholder="Leave blank to keep the current key"
                value={keys[item.key_env] ?? ""}
                onChange={(event) =>
                  setKeys((current) => ({ ...current, [item.key_env]: event.target.value }))
                }
              />
            </div>
          ))}
          <div className="grid gap-2 sm:max-w-lg">
            <Label htmlFor="search-key" className="flex items-center gap-2">
              {settings.search_key_env}
              <Badge variant={settings.search_key_set ? "secondary" : "outline"}>
                {settings.search_key_set ? `set ····${settings.search_key_last4}` : "missing"}
              </Badge>
            </Label>
            <Input
              id="search-key"
              type="password"
              autoComplete="off"
              placeholder="Tavily key, optional"
              value={searchKey}
              onChange={(event) => setSearchKey(event.target.value)}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
