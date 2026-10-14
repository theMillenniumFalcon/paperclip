"use client"

import { toast } from "sonner"

import { useDashboard } from "@/components/dashboard-context"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar"
import { revealPath } from "@/lib/api"
import { FolderOpenIcon, MoreHorizontalIcon } from "lucide-react"

export function NavDocuments({
  items,
}: {
  items: {
    name: string
    path: string
    icon: React.ReactNode
  }[]
}) {
  const { isMobile } = useSidebar()
  const { data } = useDashboard()

  async function openPath(path: string) {
    if (!data) {
      toast.error("The API is not connected, so files cannot be opened yet.")
      return
    }
    try {
      const result = await revealPath(path)
      if (result.error) toast.error(result.error)
      else toast.success(result.opened_in ? `Opened in ${result.opened_in}` : "Revealed on disk")
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not open that path")
    }
  }

  return (
    <SidebarGroup className="group-data-[collapsible=icon]:hidden">
      <SidebarGroupLabel>Home</SidebarGroupLabel>
      <SidebarMenu>
        {items.map((item) => (
          <SidebarMenuItem key={item.name}>
            <SidebarMenuButton onClick={() => void openPath(item.path)}>
              {item.icon}
              <span>{item.name}</span>
            </SidebarMenuButton>
            <DropdownMenu>
              <DropdownMenuTrigger
                render={
                  <SidebarMenuAction
                    showOnHover
                    className="aria-expanded:bg-muted"
                  />
                }
              >
                <MoreHorizontalIcon />
                <span className="sr-only">More</span>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                className="w-36"
                side={isMobile ? "bottom" : "right"}
                align={isMobile ? "end" : "start"}
              >
                <DropdownMenuItem onClick={() => void openPath(item.path)}>
                  <FolderOpenIcon />
                  <span>Open</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  )
}
