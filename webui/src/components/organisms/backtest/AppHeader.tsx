"use client";

import { useEffect, useRef } from "react";
import { Check, ChevronDown, Moon, Play, Settings2, Sun } from "lucide-react";

import { Button } from "@/components/atoms/Button";
import type { ThemeMode } from "@/types/theme";

interface AppHeaderProps {
  readonly isRunning: boolean;
  readonly isValidating: boolean;
  readonly selectedStrategy: string;
  readonly strategyOptions: string[];
  readonly isStrategyMenuOpen: boolean;
  readonly isStrategiesLoading: boolean;
  readonly strategiesError: string | null;
  readonly themeMode: ThemeMode;
  readonly canRunBacktest: boolean;
  readonly canCheckCode: boolean;
  readonly runDisabledReason?: string;
  readonly onRunBacktest: () => void;
  readonly onCheckCode: () => void;
  readonly onOpenSettings: () => void;
  readonly onToggleTheme: () => void;
  readonly onToggleStrategyMenu: () => void;
  readonly onSelectStrategy: (strategy: string) => void;
  readonly onCloseStrategyMenu: () => void;
}

const HEADER_ACTION_CLASS_NAME =
  "h-8 rounded-lg border border-border/80 bg-muted/50 text-foreground hover:bg-muted";

export function AppHeader({
  isRunning,
  isValidating,
  selectedStrategy,
  strategyOptions,
  isStrategyMenuOpen,
  isStrategiesLoading,
  strategiesError,
  themeMode,
  canRunBacktest,
  canCheckCode,
  runDisabledReason,
  onRunBacktest,
  onCheckCode,
  onOpenSettings,
  onToggleTheme,
  onToggleStrategyMenu,
  onSelectStrategy,
  onCloseStrategyMenu,
}: Readonly<AppHeaderProps>) {
  const isDarkTheme = themeMode === "dark";
  const menuRootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isStrategyMenuOpen) {
      return;
    }

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onCloseStrategyMenu();
      }
    };
    const handleClickAway = (event: MouseEvent) => {
      if (!menuRootRef.current?.contains(event.target as Node)) {
        onCloseStrategyMenu();
      }
    };

    globalThis.window.addEventListener("keydown", handleEscape);
    globalThis.window.addEventListener("mousedown", handleClickAway);
    return () => {
      globalThis.window.removeEventListener("keydown", handleEscape);
      globalThis.window.removeEventListener("mousedown", handleClickAway);
    };
  }, [isStrategyMenuOpen, onCloseStrategyMenu]);

  return (
    <header className="relative z-[13010] h-12 border-b border-border/80 bg-background/85 px-4 backdrop-blur-md sm:px-6">
      <div className="mx-auto flex h-full w-full max-w-[1680px] items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-[1.08rem] font-semibold leading-none tracking-tight text-foreground">Z*</h1>
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

          <div className="relative" ref={menuRootRef}>
            <Button
              type="button"
              variant="ghost"
              className={`${HEADER_ACTION_CLASS_NAME} gap-2 px-3`}
              onClick={onToggleStrategyMenu}
              aria-expanded={isStrategyMenuOpen}
              aria-haspopup="menu"
              title="Select strategy file"
            >
              <span className="max-w-[11rem] truncate text-left text-xs font-medium sm:text-sm">
                {selectedStrategy || "Select a strategy"}
              </span>
              <ChevronDown
                className={[
                  "h-4 w-4 transition-transform",
                  isStrategyMenuOpen ? "rotate-180" : "",
                ].join(" ")}
              />
            </Button>

            {isStrategyMenuOpen ? (
              <div className="absolute right-0 top-[calc(100%+0.55rem)] z-[14020] w-64 rounded-lg border border-border/80 bg-popover/95 p-1.5 shadow-2xl backdrop-blur-md">
                {isStrategiesLoading ? (
                  <p className="px-2 py-2 text-sm text-muted-foreground">Loading strategies...</p>
                ) : null}

                {strategiesError ? (
                  <p className="px-2 py-2 text-sm text-red-400">{strategiesError}</p>
                ) : null}

                {!isStrategiesLoading && !strategiesError && strategyOptions.length === 0 ? (
                  <p className="px-2 py-2 text-sm text-muted-foreground">No strategy files found.</p>
                ) : null}

                {!isStrategiesLoading && !strategiesError && strategyOptions.length > 0 ? (
                  <ul className="max-h-64 overflow-y-auto py-0.5">
                    {strategyOptions.map((strategy) => (
                      <li key={strategy}>
                        <button
                          type="button"
                          className="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-sm text-foreground transition-colors hover:bg-muted/70"
                          onClick={() => {
                            onSelectStrategy(strategy);
                          }}
                        >
                          <span className="truncate">{strategy}</span>
                          {strategy === selectedStrategy ? <Check className="h-4 w-4 text-emerald-400" /> : null}
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ) : null}
          </div>

          <Button
            type="button"
            variant="ghost"
            className={`${HEADER_ACTION_CLASS_NAME} gap-2 px-3`}
            onClick={onCheckCode}
            disabled={!canCheckCode}
            title={canCheckCode ? "Check code" : "Select a strategy before checking code"}
          >
            {isValidating ? "Checking..." : "Check Code"}
          </Button>

          <Button
            type="button"
            variant="ghost"
            className={`${HEADER_ACTION_CLASS_NAME} gap-2 px-3`}
            onClick={onRunBacktest}
            disabled={!canRunBacktest}
            title={runDisabledReason ?? "Run backtest"}
          >
            <Play className="h-4 w-4" />
            {isRunning ? "Running..." : "Run Backtest"}
          </Button>
        </div>
      </div>
    </header>
  );
}
