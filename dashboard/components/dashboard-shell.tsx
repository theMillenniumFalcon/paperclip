import { AppSidebar } from "@/components/app-sidebar"
import { ChatDock } from "@/components/chat-dock"
import { Cockpit } from "@/components/cockpit"
import { DashboardProvider } from "@/components/dashboard-context"
import { SiteHeader } from "@/components/site-header"
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar"

export function DashboardShell() {
  return (
    <DashboardProvider>
      <SidebarProvider
        style={
          {
            "--sidebar-width": "calc(var(--spacing) * 72)",
            "--header-height": "calc(var(--spacing) * 12)",
          } as React.CSSProperties
        }
      >
        <AppSidebar variant="inset" />
        <SidebarInset>
          <SiteHeader />
          <div className="flex flex-1 flex-col">
            <div className="@container/main flex flex-1 flex-col gap-2">
              <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
                <Cockpit />
              </div>
            </div>
          </div>
          <ChatDock />
        </SidebarInset>
      </SidebarProvider>
    </DashboardProvider>
  )
}
