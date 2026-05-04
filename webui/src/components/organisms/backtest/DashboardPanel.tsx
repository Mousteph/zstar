"use client";

import { memo } from "react";

import { EquityCurveChart } from "@/components/organisms/backtest/EquityCurveChart";
import { KpiCards } from "@/components/organisms/backtest/KpiCards";
import { KpiTable } from "@/components/organisms/backtest/KpiTable";
import { MarketOhlcvChart } from "@/components/organisms/backtest/MarketOhlcvChart";
import { RecentTradesTable } from "@/components/organisms/backtest/RecentTradesTable";
import type {
  BacktestRunResponse,
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
  readonly backtestResult: BacktestRunResponse | null;
  readonly selectedStrategy: string;
  readonly settings: BacktestSettings;
  readonly themeMode: ThemeMode;
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
  backtestResult,
  selectedStrategy,
  settings,
  themeMode,
}: Readonly<DashboardPanelProps>) {
  const csvMeta = backtestResult?.meta ?? null;
  const yahooSymbol = settings.symbol.trim().toUpperCase() || "—";
  const yahooInterval = settings.interval.trim() || "—";
  const yahooStartDate = formatHeroDate(settings.startDate);
  const yahooEndDate = formatHeroDate(settings.endDate);
  const csvStartDate = csvMeta ? formatHeroDate(csvMeta.start_date) : "—";
  const csvEndDate = csvMeta ? formatHeroDate(csvMeta.end_date) : "—";
  const csvInterval = csvMeta?.interval ?? "—";
  const csvFilename = settings.csvFilename || "—";
  const heroSourceLine =
    settings.dataSource === "csv"
      ? `CSV - ${csvFilename}`
      : `Yahoo API - ${yahooSymbol} - ${yahooInterval}`;
  const csvDateLine = csvMeta
    ? `${csvInterval} - ${csvStartDate} - ${csvEndDate}`
    : "Run a CSV backtest to display timeframe and date range";
  const heroDateLine =
    settings.dataSource === "csv" ? csvDateLine : `${yahooStartDate} - ${yahooEndDate}`;

  const firstValidationIssue =
    validationResult && !validationResult.ready_to_backtest && validationResult.issues.length > 0
      ? validationResult.issues[0]
      : null;

  const heroState = (() => {
    if (firstValidationIssue) {
      return {
        tone: "error" as const,
        title: "Strategy Validation Error",
        message: firstValidationIssue.message,
        meta: "[error] [" + firstValidationIssue.category + "] " + firstValidationIssue.file + (firstValidationIssue.line === null ? "" : ":" + firstValidationIssue.line),
      };
    }

    if (isValidating) {
      return {
        tone: "ready" as const,
        title: "Strategy Validation",
        message: "Checking strategy code...",
        meta: null,
      };
    }

    if (runStatus?.tone === "success") {
      return {
        tone: "success" as const,
        title: "Backtest Status",
        message: runStatus.message,
        meta: null,
      };
    }

    if (runStatus?.tone === "error") {
      return {
        tone: "error" as const,
        title: "Backtest Error",
        message: runStatus.message,
        meta: null,
      };
    }

    if (validationResult?.ready_to_backtest) {
      return {
        tone: "ready" as const,
        title: "Strategy Validation",
        message: "Ready to backtest",
        meta: null,
      };
    }

    return null;
  })();

  const getHeroStateClass = (state: typeof heroState): string => {
    if (!state) return "";
    if (state.tone === "error") return "border-red-500/30 bg-red-500/10 text-red-100 shadow-[0_0_0_1px_rgba(239,68,68,0.08)]";
    if (state.tone === "success") return "border-emerald-400/30 bg-emerald-400/10 text-emerald-50 shadow-[0_0_0_1px_rgba(52,211,153,0.08)]";
    return "border-blue-500/30 bg-blue-500/10 text-blue-50 shadow-[0_0_0_1px_rgba(59,130,246,0.08)]";
  };

  const heroStateClass = getHeroStateClass(heroState);

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
              Backtest Snapshot{' '}
              <span className="ml-2 inline-block normal-case tracking-[0.08em] text-foreground/80">
                {selectedStrategy}
              </span>
            </p>
            <h2 className="hero-title-animation mt-3 font-display text-[clamp(3.75rem,12vw,10rem)] font-semibold leading-[0.9] tracking-[-0.04em] text-foreground">
              Backtest
            </h2>
            <p className="hero-line-animation-delay-1 mt-5 text-base font-medium tracking-wide text-foreground/85 sm:text-lg">
              {heroSourceLine}
            </p>
            <p className="hero-line-animation-delay-2 mt-1 text-sm tracking-wide text-muted-foreground sm:text-base">
              {heroDateLine}
            </p>
            {heroState ? (
              <div
                className={[
                  "status-line-animation mt-5 w-full rounded-2xl border px-4 py-3 backdrop-blur-sm",
                  heroStateClass,
                ].join(" ")}
                role={heroState.tone === "error" ? "alert" : undefined}
                aria-live={heroState.tone === "error" ? "assertive" : "polite"}
              >
                <p className="text-[0.65rem] font-medium uppercase tracking-[0.22em] text-current/70">
                  {heroState.title}
                </p>
                {heroState.meta ? (
                  <p className="mt-2 text-xs uppercase tracking-[0.16em] text-current/75">{heroState.meta}</p>
                ) : null}
                <p className="mt-2 whitespace-pre-wrap font-mono text-xs leading-5 text-current sm:text-sm">
                  {heroState.message}
                </p>
              </div>
            ) : null}
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
