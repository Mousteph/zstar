import { useEffect } from "react";
import { X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useScrollLock } from "@/hooks/useScrollLock";
import { TIMEFRAME_OPTIONS } from "@/features/backtest/constants";
import type { BacktestSettings } from "@/types/backtest";

interface BacktestSettingsPanelProps {
  readonly isOpen: boolean;
  readonly settings: BacktestSettings;
  readonly onClose: () => void;
  readonly onSettingsChange: (settings: BacktestSettings) => void;
}

function updateNumberField(value: string, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

const SETTINGS_FIELD_CLASS_NAME =
  "w-full rounded-lg border border-border/80 bg-background/80 px-3 py-2.5 text-sm text-foreground outline-none transition-colors focus:border-ring";

export function BacktestSettingsPanel({
  isOpen,
  settings,
  onClose,
  onSettingsChange,
}: BacktestSettingsPanelProps) {
  useScrollLock(isOpen);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    globalThis.window.addEventListener("keydown", handleEscape);

    return () => {
      globalThis.window.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen, onClose]);

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-[13000]">
      <button
        type="button"
        aria-label="Close backtest settings dialog"
        className="absolute inset-0 bg-black/45 backdrop-blur-[2px]"
        onClick={onClose}
      />
      <div className="relative z-10 flex h-full items-center justify-center p-4">
        <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl border border-border/80 bg-gradient-to-b from-slate-50 via-white to-slate-100 p-5 shadow-2xl dark:from-[#0d1322] dark:via-[#090d18] dark:to-[#080b14] sm:p-6">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-[1.65rem] font-semibold tracking-tight text-foreground">Backtest Settings</h2>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 rounded-lg border border-border/80 bg-muted/60 text-foreground hover:bg-muted"
            onClick={onClose}
            aria-label="Close settings"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="space-y-4">
          <label className="block">
            <span className="mb-1.5 block text-sm text-muted-foreground">Symbol</span>
            <input
              value={settings.symbol}
              onChange={(event) =>
                onSettingsChange({
                  ...settings,
                  symbol: event.target.value.toUpperCase(),
                })
              }
              className={SETTINGS_FIELD_CLASS_NAME}
              placeholder="AAPL"
            />
          </label>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label className="block">
              <span className="mb-1.5 block text-sm text-muted-foreground">Start Date</span>
              <input
                type="date"
                value={settings.startDate}
                onChange={(event) =>
                  onSettingsChange({
                    ...settings,
                    startDate: event.target.value,
                  })
                }
                className={SETTINGS_FIELD_CLASS_NAME}
              />
            </label>

            <label className="block">
              <span className="mb-1.5 block text-sm text-muted-foreground">End Date</span>
              <input
                type="date"
                value={settings.endDate}
                onChange={(event) =>
                  onSettingsChange({
                    ...settings,
                    endDate: event.target.value,
                  })
                }
                className={SETTINGS_FIELD_CLASS_NAME}
              />
            </label>
          </div>

          <label className="block">
            <span className="mb-1.5 block text-sm text-muted-foreground">Timeframe</span>
            <select
              value={settings.interval}
              onChange={(event) =>
                onSettingsChange({
                  ...settings,
                  interval: event.target.value,
                })
              }
              className={SETTINGS_FIELD_CLASS_NAME}
            >
              {TIMEFRAME_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="mb-1.5 block text-sm text-muted-foreground">Initial Balance</span>
            <input
              type="number"
              min={1}
              value={settings.initialBalance}
              onChange={(event) =>
                onSettingsChange({
                  ...settings,
                  initialBalance: updateNumberField(event.target.value, settings.initialBalance),
                })
              }
              className={SETTINGS_FIELD_CLASS_NAME}
            />
          </label>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label className="block">
              <span className="mb-1.5 block text-sm text-muted-foreground">Entry Fee %</span>
              <input
                type="number"
                min={0}
                step="0.01"
                value={settings.entryFeePct}
                onChange={(event) =>
                  onSettingsChange({
                    ...settings,
                    entryFeePct: updateNumberField(event.target.value, settings.entryFeePct),
                  })
                }
                className={SETTINGS_FIELD_CLASS_NAME}
              />
            </label>

            <label className="block">
              <span className="mb-1.5 block text-sm text-muted-foreground">Exit Fee %</span>
              <input
                type="number"
                min={0}
                step="0.01"
                value={settings.exitFeePct}
                onChange={(event) =>
                  onSettingsChange({
                    ...settings,
                    exitFeePct: updateNumberField(event.target.value, settings.exitFeePct),
                  })
                }
                className={SETTINGS_FIELD_CLASS_NAME}
              />
            </label>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label className="block">
              <span className="mb-1.5 block text-sm text-muted-foreground">Slippage %</span>
              <input
                type="number"
                min={0}
                step="0.01"
                value={settings.slippagePct}
                onChange={(event) =>
                  onSettingsChange({
                    ...settings,
                    slippagePct: updateNumberField(event.target.value, settings.slippagePct),
                  })
                }
                className={SETTINGS_FIELD_CLASS_NAME}
              />
            </label>

            <label className="block">
              <span className="mb-1.5 block text-sm text-muted-foreground">Slippage Seed</span>
              <input
                value={settings.slippageSeed}
                onChange={(event) =>
                  onSettingsChange({
                    ...settings,
                    slippageSeed: event.target.value,
                  })
                }
                className={SETTINGS_FIELD_CLASS_NAME}
                placeholder="optional"
              />
            </label>
          </div>
        </div>

        <div className="mt-7">
          <Button
            type="button"
            variant="ghost"
            className="h-10 w-full rounded-lg border border-border/80 bg-muted/60 text-foreground hover:bg-muted"
            onClick={onClose}
          >
            Done
          </Button>
        </div>
      </div>
    </div>
  </div>
  );
}
