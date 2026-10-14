"use client"

import * as React from "react"

import { useDashboard } from "@/components/dashboard-context"
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import type { Section } from "@/lib/types"

export function NavSecondary({
  items,
  ...props
}: {
  items: {
    title: string
    section?: Section
    action?: "chat" | "refresh"
    icon: React.ReactNode
  }[]
} & React.ComponentPropsWithoutRef<typeof SidebarGroup>) {
  const { section, setSection, setChatOpen, refresh } = useDashboard()
  return (
    <SidebarGroup {...props}>
      <SidebarGroupContent>
        <SidebarMenu>
          {items.map((item) => (
            <SidebarMenuItem key={item.title}>
              <SidebarMenuButton
                isActive={item.section != null && section === item.section}
                onClick={() => {
                  if (item.section) setSection(item.section)
                  if (item.action === "chat") setChatOpen(true)
                  if (item.action === "refresh") void refresh()
                }}
              >
                {item.icon}
                <span>{item.title}</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}
