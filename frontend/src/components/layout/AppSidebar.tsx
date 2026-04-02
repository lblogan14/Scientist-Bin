import { Link, useLocation } from "react-router";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  BarChart3,
  Boxes,
  FlaskConical,
  LayoutDashboard,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { listExperiments } from "@/lib/api-client";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/experiments", label: "Experiments", icon: FlaskConical },
  { to: "/monitor", label: "Training", icon: Activity },
  { to: "/results", label: "Results", icon: BarChart3 },
  { to: "/models", label: "Models", icon: Boxes },
];

export function AppSidebar() {
  const { pathname } = useLocation();

  // Check for experiments needing plan review
  const { data: hasPlanReview } = useQuery({
    queryKey: ["experiments", "plan-review-check"],
    queryFn: async () => {
      const { experiments } = await listExperiments();
      return experiments.some((e) => e.phase === "plan_review");
    },
    refetchInterval: 10_000,
  });

  return (
    <Sidebar>
      <SidebarHeader className="p-4">
        <h1 className="text-lg font-bold">Scientist-Bin</h1>
        <p className="text-muted-foreground text-xs">ML Training Agent</p>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => {
                const active =
                  item.to === "/"
                    ? pathname === "/"
                    : pathname.startsWith(item.to);
                const showDot = item.to === "/monitor" && hasPlanReview;
                return (
                  <SidebarMenuItem key={item.to}>
                    <SidebarMenuButton asChild isActive={active}>
                      <Link to={item.to}>
                        <item.icon className="size-4" />
                        <span className="flex-1">{item.label}</span>
                        {showDot && (
                          <span className="size-2 shrink-0 animate-pulse rounded-full bg-amber-500" />
                        )}
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
