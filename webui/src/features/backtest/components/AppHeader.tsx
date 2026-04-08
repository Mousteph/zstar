import { Code2, Moon, Play, Settings2, Sun } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { ThemeMode } from "@/types/theme";

interface AppHeaderProps {
  readonly isRunning: boolean;
  readonly isCodeVisible: boolean;
  readonly themeMode: ThemeMode;
  readonly onRunBacktest: () => void;
  readonly onOpenSettings: () => void;
  readonly onToggleCodeVisibility: () => void;
  readonly onToggleTheme: () => void;
}

const HEADER_ACTION_CLASS_NAME =
  "h-8 rounded-lg border border-border/80 bg-muted/50 text-foreground hover:bg-muted";

export function AppHeader({
  isRunning,
  isCodeVisible,
  themeMode,
  onRunBacktest,
  onOpenSettings,
  onToggleCodeVisibility,
  onToggleTheme,
}: AppHeaderProps) {
  const isDarkTheme = themeMode === "dark";

  return (
    <header className="h-12 border-b border-border/80 bg-background/85 px-4 backdrop-blur-md sm:px-6">
      <div className="mx-auto flex h-full w-full max-w-[1680px] items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-[1.08rem] font-semibold leading-none tracking-tight text-foreground">ZStar</h1>
          <span className="text-sm font-medium uppercase tracking-[0.14em] text-muted-foreground">backtest</span>
        </div>

        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className={`${HEADER_ACTION_CLASS_NAME} w-8 px-0`}
            onClick={onOpenSettings}
            aria-label="Open settings"
            title="Open settings"
          >
            <Settings2 className="h-4 w-4" />
          </Button>

          <Button
            type="button"
            variant="ghost"
            size="icon"
            className={`${HEADER_ACTION_CLASS_NAME} w-8 px-0`}
            onClick={onToggleTheme}
            aria-label={isDarkTheme ? "Switch to light theme" : "Switch to dark theme"}
            title={isDarkTheme ? "Switch to light theme" : "Switch to dark theme"}
          >
            {isDarkTheme ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>

          <Button
            type="button"
            variant="ghost"
            className={`${HEADER_ACTION_CLASS_NAME} gap-2 px-3`}
            onClick={onRunBacktest}
            disabled={isRunning}
          >
            <Play className="h-4 w-4" />
            {isRunning ? "Running..." : "Run Backtest"}
          </Button>

          <Button
            type="button"
            variant="ghost"
            className={`${HEADER_ACTION_CLASS_NAME} gap-2 px-3`}
            onClick={onToggleCodeVisibility}
            aria-label={isCodeVisible ? "Hide code" : "Show code"}
            title={isCodeVisible ? "Hide code" : "Show code"}
          >
            <Code2 className="h-4 w-4" />
            {isCodeVisible ? "Hide code" : "Show code"}
          </Button>
        </div>
      </div>
    </header>
  );
}
