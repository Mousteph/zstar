"use client";

import { useEffect } from "react";
import { Upload, X } from "lucide-react";

import { Button } from "@/components/atoms/Button";
import { TIMEFRAME_OPTIONS } from "@/features/backtest/constants";
import { useScrollLock } from "@/hooks/useScrollLock";
import type { BacktestSettings } from "@/types/backtest";

interface BacktestSettingsPanelProps {
  readonly isOpen: boolean;
  readonly settings: BacktestSettings;
  readonly csvFiles: string[];
  readonly csvFilesError: string | null;
  readonly isCsvFilesLoading: boolean;
  readonly isCsvUploading: boolean;
  readonly onClose: () => void;
  readonly onSettingsChange: (settings: BacktestSettings) => void;
  readonly onLoadCsvFiles: () => Promise<void>;
  readonly onUploadCsv: (file: File) => Promise<void>;
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
  csvFiles,
  csvFilesError,
  isCsvFilesLoading,
  isCsvUploading,
  onClose,
  onSettingsChange,
  onLoadCsvFiles,
  onUploadCsv,
}: Readonly<BacktestSettingsPanelProps>) {
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

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    void onLoadCsvFiles();
  }, [isOpen, onLoadCsvFiles]);

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
        <div className="settings-panel-surface relative max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-border/80 p-5 shadow-2xl sm:p-6">
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
            <div>
              <span className="mb-1.5 block text-sm text-muted-foreground">Source</span>
              <div className="grid grid-cols-2 gap-2 rounded-lg border border-border/80 bg-background/80 p-1">
                {(["yahoo", "csv"] as const).map((source) => (
                  <button
                    key={source}
                    type="button"
                    className={`h-9 rounded-md text-sm font-medium transition-colors ${
                      settings.dataSource === source
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    }`}
                    onClick={() =>
                      onSettingsChange({
                        ...settings,
                        dataSource: source,
                        csvFilename: source === "csv" && !settings.csvFilename && csvFiles.length > 0 ? csvFiles[0] : settings.csvFilename,
                      })
                    }
                  >
                    {source === "yahoo" ? "Yahoo" : "CSV"}
                  </button>
                ))}
              </div>
            </div>

            {settings.dataSource === "yahoo" ? (
              <>
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
              </>
            ) : (
              <div className="space-y-4">
                <label className="block">
                  <span className="mb-1.5 block text-sm text-muted-foreground">CSV File</span>
                  <select
                    value={settings.csvFilename}
                    onChange={(event) =>
                      onSettingsChange({
                        ...settings,
                        csvFilename: event.target.value,
                      })
                    }
                    className={SETTINGS_FIELD_CLASS_NAME}
                    disabled={isCsvFilesLoading || csvFiles.length === 0}
                  >
                    <option value="">{isCsvFilesLoading ? "Loading CSV files..." : "Select a CSV file"}</option>
                    {csvFiles.map((filename) => (
                      <option key={filename} value={filename}>
                        {filename}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="flex cursor-pointer items-center justify-center gap-2 rounded-lg border border-dashed border-border/90 bg-background/70 px-3 py-3 text-sm font-medium text-foreground transition-colors hover:bg-muted/70">
                  <Upload className="h-4 w-4" />
                  <span>{isCsvUploading ? "Uploading..." : "Upload CSV"}</span>
                  <input
                    type="file"
                    accept=".csv,text/csv"
                    className="sr-only"
                    disabled={isCsvUploading}
                    onChange={(event) => {
                      const file = event.target.files?.[0];
                      event.target.value = "";
                      if (file) {
                        void onUploadCsv(file);
                      }
                    }}
                  />
                </label>

                {csvFilesError ? <p className="text-sm text-destructive">{csvFilesError}</p> : null}
              </div>
            )}

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
