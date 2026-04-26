"use client";

import { memo } from "react";

import { EquityCurveChart } from "@/components/organisms/backtest/EquityCurveChart";
import { KpiCards } from "@/components/organisms/backtest/KpiCards";
import { KpiTable } from "@/components/organisms/backtest/KpiTable";
import { MarketOhlcvChart } from "@/components/organisms/backtest/MarketOhlcvChart";
import { RecentTradesTable } from "@/components/organisms/backtest/RecentTradesTable";
import type {
  BacktestRunStatus,
  BacktestSettings,
  EquityPoint,
  KpiMetric,
  KpiRow,
  MarketOhlcvPoint,
  StrategyValidationResult,
  Trade,
} from "@/types/backtest";
import type { ThemeMode } from "@/types/theme";

interface DashboardPanelProps {
  readonly equityData: EquityPoint[];
  readonly marketOhlcvData: MarketOhlcvPoint[];
  readonly kpiMetrics: KpiMetric[];
  readonly kpiRows: KpiRow[];
  readonly recentTrades: Trade[];
  readonly runStatus: BacktestRunStatus | null;
  readonly validationResult: StrategyValidationResult | null;
  readonly isValidating: boolean;
  readonly selectedStrategy: string;
  readonly settings: BacktestSettings;
  readonly themeMode: ThemeMode;
  readonly onExportValidationReport: (format: "txt" | "json") => void;
}

function formatHeroDate(dateValue: string): string {
  const [year, month, day] = dateValue.split("-").map(Number);
  if (!Number.isFinite(year) || !Number.isFinite(month) || !Number.isFinite(day)) {
    return dateValue;
  }

  return new Intl.DateTimeFormat("en-US", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(Date.UTC(year, month - 1, day)));
}

export const DashboardPanel = memo(function DashboardPanel({
  equityData,
  marketOhlcvData,
  kpiMetrics,
  kpiRows,
  recentTrades,
  runStatus,
  validationResult,
  isValidating,
  selectedStrategy,
  settings,
  themeMode,
  onExportValidationReport,
}: Readonly<DashboardPanelProps>) {
  const symbol = settings.symbol.trim().toUpperCase() || "—";
  const interval = settings.interval.trim() || "—";
  const startDate = formatHeroDate(settings.startDate);
  const endDate = formatHeroDate(settings.endDate);

  return (
    <div className="dashboard-panel-surface relative isolate h-full min-h-0 overflow-x-hidden overflow-y-auto px-5 pb-8 pt-5 sm:px-8 sm:pb-10 sm:pt-7 lg:px-10">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-28 top-[14%] h-80 w-80 rounded-full bg-emerald-400/20 dark:bg-emerald-400/10 blur-3xl" />
        <div className="absolute -right-20 top-[4%] h-72 w-72 rounded-full bg-sky-500/20 dark:bg-sky-500/10 blur-3xl" />
        <div className="absolute left-[18%] top-[58%] h-96 w-96 rounded-full bg-indigo-500/10 dark:bg-indigo-500/5 blur-3xl" />
      </div>

      <div className="relative space-y-9 sm:space-y-10">
        <section className="relative overflow-hidden border-b border-border/80 px-2 pb-9 pt-8 sm:px-4 sm:pb-11 sm:pt-10 lg:px-6 lg:pb-12 lg:pt-12">
          <div className="relative flex min-h-[34svh] flex-col justify-center lg:min-h-[44svh]">
            <p className="hero-line-animation text-[0.7rem] uppercase tracking-[0.24em] text-muted-foreground">
              Backtest Snapshot
              <span className="ml-2 inline-block normal-case tracking-[0.08em] text-foreground/80">
                {selectedStrategy}
              </span>
            </p>
            <h2 className="hero-title-animation mt-3 font-display text-[clamp(3.75rem,12vw,10rem)] font-semibold leading-[0.9] tracking-[-0.04em] text-foreground">
              Backtest
            </h2>
            <p className="hero-line-animation-delay-1 mt-5 text-base font-medium tracking-wide text-foreground/85 sm:text-lg">
              {symbol} - {interval}
            </p>
            <p className="hero-line-animation-delay-2 mt-1 text-sm tracking-wide text-muted-foreground sm:text-base">
              {startDate} - {endDate}
            </p>
            <div className="status-line-animation mt-5 w-full space-y-3">
              <div
                className={[
                  "w-full rounded-2xl border px-4 py-3 backdrop-blur-sm",
                  validationResult?.ready_to_backtest
                    ? "border-blue-500/30 bg-blue-500/10 text-blue-50 shadow-[0_0_0_1px_rgba(59,130,246,0.08)]"
                    : "border-red-500/30 bg-red-500/10 text-red-100 shadow-[0_0_0_1px_rgba(239,68,68,0.08)]",
                ].join(" ")}
                role={validationResult && !validationResult.ready_to_backtest ? "alert" : undefined}
                aria-live={validationResult && !validationResult.ready_to_backtest ? "assertive" : "polite"}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-1">
                    <p className="text-[0.65rem] font-medium uppercase tracking-[0.22em] text-current/70">
                      Strategy Validation
                    </p>
                    <p className="whitespace-pre-line text-sm font-medium leading-6 text-current sm:text-[0.95rem]">
                      {isValidating
                        ? "Checking strategy code..."
                        : validationResult
                          ? validationResult.ready_to_backtest
                            ? "Ready to backtest"
                            : validationResult.summary_text
                          : "Run Check Code to validate strategy file."}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      className="rounded-md border border-current/30 px-2 py-1 text-xs font-medium disabled:cursor-not-allowed disabled:opacity-50"
                      onClick={() => {
                        onExportValidationReport("txt");
                      }}
                      disabled={!validationResult}
                    >
                      Export TXT
                    </button>
                    <button
                      type="button"
                      className="rounded-md border border-current/30 px-2 py-1 text-xs font-medium disabled:cursor-not-allowed disabled:opacity-50"
                      onClick={() => {
                        onExportValidationReport("json");
                      }}
                      disabled={!validationResult}
                    >
                      Export JSON
                    </button>
                  </div>
                </div>

                {validationResult && validationResult.issues.length > 0 ? (
                  <ul className="mt-3 space-y-2 border-t border-current/20 pt-3">
                    {validationResult.issues.map((issue, index) => (
                      <li key={`${issue.file}-${issue.line ?? "na"}-${issue.category}-${index}`}>
                        <p className="text-xs uppercase tracking-[0.16em] text-current/75">
                          [error] [{issue.category}] {issue.file}
                          {issue.line === null ? "" : `:${issue.line}`}
                        </p>
                        <p className="whitespace-pre-wrap font-mono text-xs leading-5 text-current sm:text-sm">
                          {issue.message}
                        </p>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>

              {runStatus ? (
                <div
                  className={[
                    "inline-flex max-w-[min(100%,34rem)] items-start gap-3 self-start rounded-2xl border px-4 py-3 backdrop-blur-sm",
                    runStatus.tone === "error"
                      ? "border-red-500/30 bg-red-500/10 text-red-100 shadow-[0_0_0_1px_rgba(239,68,68,0.08)]"
                      : "border-emerald-400/30 bg-emerald-400/10 text-emerald-50 shadow-[0_0_0_1px_rgba(52,211,153,0.08)]",
                  ].join(" ")}
                  role={runStatus.tone === "error" ? "alert" : undefined}
                  aria-live={runStatus.tone === "error" ? "assertive" : "polite"}
                >
                  <span
                    className={[
                      "mt-1 h-2 w-2 shrink-0 rounded-full",
                      runStatus.tone === "error"
                        ? "bg-red-400 shadow-[0_0_18px_rgba(248,113,113,0.75)]"
                        : "bg-emerald-300 shadow-[0_0_18px_rgba(110,231,183,0.75)]",
                    ].join(" ")}
                    aria-hidden="true"
                  />
                  <div className="space-y-1">
                    <p className="text-[0.65rem] font-medium uppercase tracking-[0.22em] text-current/70">
                      {runStatus.tone === "error" ? "Backtest Error" : "Backtest Status"}
                    </p>
                    <p className="whitespace-pre-line text-sm font-medium leading-6 text-current sm:text-[0.95rem]">
                      {runStatus.message}
                    </p>
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        </section>

        <EquityCurveChart data={equityData} />
        <KpiCards metrics={kpiMetrics} />
        <KpiTable rows={kpiRows} />
        <MarketOhlcvChart data={marketOhlcvData} trades={recentTrades} themeMode={themeMode} />
        <RecentTradesTable trades={recentTrades} />
      </div>
    </div>
  );
});
