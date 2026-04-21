"use client";

import { useMemo } from "react";

import { AppHeader } from "@/components/organisms/backtest/AppHeader";
import { BacktestSettingsPanel } from "@/components/organisms/backtest/BacktestSettingsPanel";
import { DashboardPanel } from "@/components/organisms/backtest/DashboardPanel";
import { useThemeModeSync } from "@/hooks/useThemeModeSync";
import { mapKpiRows, mapSummaryKpis } from "@/lib/backtest/dashboardMappers";
import { useBacktestStore } from "@/stores/useBacktestStore";
import { useUIStore } from "@/stores/useUIStore";
import type { EquityPoint, KpiMetric, KpiRow, MarketOhlcvPoint, Trade } from "@/types/backtest";

const EMPTY_EQUITY_DATA: EquityPoint[] = [];
const EMPTY_MARKET_OHLCV_DATA: MarketOhlcvPoint[] = [];
const EMPTY_TRADES: Trade[] = [];
const EMPTY_KPI_METRICS: KpiMetric[] = [];
const EMPTY_KPI_ROWS: KpiRow[] = [];

export function BacktestWorkbench() {
  const {
    isSettingsOpen,
    themeMode,
    openSettings,
    closeSettings,
    toggleThemeMode,
  } = useUIStore();

  const { isRunning, settings, backtestResult, runStatus, setSettings, runCurrentBacktest } =
    useBacktestStore();

  useThemeModeSync(themeMode);

  const kpiMetrics = useMemo(() => (backtestResult ? mapSummaryKpis(backtestResult) : EMPTY_KPI_METRICS), [backtestResult]);
  const kpiRows = useMemo(() => (backtestResult ? mapKpiRows(backtestResult) : EMPTY_KPI_ROWS), [backtestResult]);
  const equityData = backtestResult?.equity_curve ?? EMPTY_EQUITY_DATA;
  const marketOhlcvData = backtestResult?.market_ohlcv ?? EMPTY_MARKET_OHLCV_DATA;
  const recentTrades = backtestResult?.trades ?? EMPTY_TRADES;

  const dashboardPanel = (
    <DashboardPanel
      equityData={equityData}
      marketOhlcvData={marketOhlcvData}
      kpiMetrics={kpiMetrics}
      kpiRows={kpiRows}
      recentTrades={recentTrades}
      runStatus={runStatus}
      settings={settings}
      themeMode={themeMode}
    />
  );

  return (
    <div className="h-screen w-full bg-background text-foreground flex flex-col overflow-hidden">
      <AppHeader
        isRunning={isRunning}
        themeMode={themeMode}
        onRunBacktest={() => {
          void runCurrentBacktest();
        }}
        onOpenSettings={openSettings}
        onToggleTheme={toggleThemeMode}
      />

      <main className="flex-1 overflow-hidden">{dashboardPanel}</main>

      <BacktestSettingsPanel
        isOpen={isSettingsOpen}
        settings={settings}
        onSettingsChange={setSettings}
        onClose={closeSettings}
      />
    </div>
  );
}
