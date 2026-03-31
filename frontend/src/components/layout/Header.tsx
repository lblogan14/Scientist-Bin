import { useQuery } from "@tanstack/react-query";
import { FlaskConical, Moon, PanelLeft, Sun } from "lucide-react";
import { checkHealth } from "@/lib/api-client";
import { type Theme, useAppStore } from "@/stores/app-store";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useSidebar } from "@/components/ui/sidebar";

const themeOptions: { value: Theme; label: string; icon: typeof Sun }[] = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "science", label: "Science", icon: FlaskConical },
];

export function Header() {
  const { toggleSidebar } = useSidebar();
  const { theme, setTheme } = useAppStore();

  const { data: health, isError } = useQuery({
    queryKey: ["health"],
    queryFn: checkHealth,
    refetchInterval: 30_000,
    retry: false,
  });

  const healthColor = isError
    ? "bg-red-500"
    : health?.status === "ok"
      ? "bg-green-500"
      : "bg-yellow-500";

  const healthLabel = isError
    ? "Backend unavailable"
    : health?.status === "ok"
      ? "Backend healthy"
      : "Backend status unknown";

  const currentThemeOption = themeOptions.find((t) => t.value === theme);
  const ThemeIcon = currentThemeOption?.icon ?? Sun;

  return (
    <header className="border-border flex h-14 items-center gap-4 border-b px-6">
      <Button variant="ghost" size="icon" onClick={toggleSidebar}>
        <PanelLeft className="size-4" />
      </Button>

      <div className="flex-1" />

      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex items-center gap-2">
            <span className={`size-2 rounded-full ${healthColor}`} />
            <span className="text-muted-foreground text-xs">{healthLabel}</span>
          </div>
        </TooltipTrigger>
        <TooltipContent>{healthLabel}</TooltipContent>
      </Tooltip>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon">
            <ThemeIcon className="size-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          {themeOptions.map((option) => (
            <DropdownMenuItem
              key={option.value}
              onClick={() => setTheme(option.value)}
            >
              <option.icon className="mr-2 size-4" />
              {option.label}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}
