"use client"

import { NavDocuments } from "@/components/nav-documents"
import { NavMain } from "@/components/nav-main"
import { NavSecondary } from "@/components/nav-secondary"
import { NavUser } from "@/components/nav-user"
import { useDashboard } from "@/components/dashboard-context"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import {
  BrainIcon,
  ChartBarIcon,
  DatabaseIcon,
  FileTextIcon,
  FolderIcon,
  LayoutDashboardIcon,
  ListIcon,
  MessageSquareIcon,
  PaperclipIcon,
  RefreshCwIcon,
  Settings2Icon,
  SquareTerminalIcon,
  WalletIcon,
} from "lucide-react"

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { data, setSection } = useDashboard()
  const provider = data?.provider ?? "paperclip"
  const model = data?.model ?? "waiting for API"

  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              className="data-[slot=sidebar-menu-button]:p-1.5!"
              onClick={() => setSection("overview")}
            >
              <PaperclipIcon className="size-5!" />
              <span className="text-base font-semibold">Paperclip</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain
          items={[
            { title: "Overview", section: "overview", icon: <LayoutDashboardIcon /> },
            { title: "Turns", section: "turns", icon: <ListIcon /> },
            { title: "Memory", section: "memory", icon: <BrainIcon /> },
            { title: "Tools", section: "tools", icon: <SquareTerminalIcon /> },
            { title: "Database", section: "database", icon: <DatabaseIcon /> },
            { title: "Evals", section: "evals", icon: <ChartBarIcon /> },
            { title: "Spend", section: "spend", icon: <WalletIcon /> },
          ]}
        />
        <NavDocuments
          items={[
            { name: "state.db", path: "state.db", icon: <DatabaseIcon /> },
            { name: "Traces", path: "traces", icon: <FolderIcon /> },
            { name: "Outbox", path: "outbox", icon: <FileTextIcon /> },
            { name: "SOUL.md", path: "SOUL.md", icon: <FileTextIcon /> },
          ]}
        />
        <NavSecondary
          className="mt-auto"
          items={[
            { title: "Settings", section: "settings", icon: <Settings2Icon /> },
            { title: "Chat", action: "chat", icon: <MessageSquareIcon /> },
            { title: "Refresh", action: "refresh", icon: <RefreshCwIcon /> },
          ]}
        />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={{ name: provider, email: model }} />
      </SidebarFooter>
    </Sidebar>
  )
}
