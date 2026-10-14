"use client"

import { Button } from "@/components/ui/button"
import { useDashboard } from "@/components/dashboard-context"
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import type { Section } from "@/lib/types"
import { CirclePlusIcon, MailIcon } from "lucide-react"

export function NavMain({
  items,
}: {
  items: {
    title: string
    section: Section
    icon?: React.ReactNode
  }[]
}) {
  const { section, setSection, setChatOpen } = useDashboard()
  return (
    <SidebarGroup>
      <SidebarGroupContent className="flex flex-col gap-2">
        <SidebarMenu>
          <SidebarMenuItem className="flex items-center gap-2">
            <SidebarMenuButton
              tooltip="Open chat"
              className="min-w-8 bg-primary text-primary-foreground duration-200 ease-linear hover:bg-primary/90 hover:text-primary-foreground active:bg-primary/90 active:text-primary-foreground"
              onClick={() => setChatOpen(true)}
            >
              <CirclePlusIcon />
              <span>Open chat</span>
            </SidebarMenuButton>
            <Button
              size="icon"
              className="size-8 group-data-[collapsible=icon]:opacity-0"
              variant="outline"
              onClick={() => {
                setSection("memory")
                setChatOpen(false)
              }}
            >
              <MailIcon />
              <span className="sr-only">Inbox</span>
            </Button>
          </SidebarMenuItem>
        </SidebarMenu>
        <SidebarMenu>
          {items.map((item) => (
            <SidebarMenuItem key={item.section}>
              <SidebarMenuButton
                tooltip={item.title}
                isActive={section === item.section}
                onClick={() => setSection(item.section)}
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
