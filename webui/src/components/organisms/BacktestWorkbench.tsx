"use client";

import { useCallback, useMemo } from "react";
import type { Layout } from "react-resizable-panels";

import { AIAssistantHud } from "@/components/organisms/ai-hud/AIAssistantHud";
import { AppHeader } from "@/components/organisms/backtest/AppHeader";
import { BacktestSettingsPanel } from "@/components/organisms/backtest/BacktestSettingsPanel";
import { DashboardPanel } from "@/components/organisms/backtest/DashboardPanel";
import { EditorPanel } from "@/components/organisms/backtest/EditorPanel";
import { BacktestWorkspaceTemplate } from "@/components/templates/BacktestWorkspaceTemplate";
import { useDesktopLayoutSync } from "@/hooks/useDesktopLayoutSync";
import { useThemeModeSync } from "@/hooks/useThemeModeSync";
import { mapKpiRows, mapSummaryKpis } from "@/lib/backtest/dashboardMappers";
import { useBacktestStore } from "@/stores/useBacktestStore";
import { DEFAULT_DASHBOARD_PANEL_SIZE, useUIStore } from "@/stores/useUIStore";
import type { EquityPoint, KpiMetric, KpiRow, MarketOhlcvPoint, Trade } from "@/types/backtest";

const EMPTY_EQUITY_DATA: EquityPoint[] = [];
const EMPTY_MARKET_OHLCV_DATA: MarketOhlcvPoint[] = [];
const EMPTY_TRADES: Trade[] = [];
const EMPTY_KPI_METRICS: KpiMetric[] = [];
const EMPTY_KPI_ROWS: KpiRow[] = [];

export function BacktestWorkbench() {
  const {
    isSettingsOpen,
    isCodeVisible,
    dashboardPanelSize,
    themeMode,
    isDesktopLayout,
    openSettings,
    closeSettings,
    toggleCodeVisibility,
    setDashboardPanelSize,
    toggleThemeMode,
    setDesktopLayout,
  } = useUIStore();

  const { isRunning, settings, strategyCode, backtestResult, runStatus, setSettings, setStrategyCode, runCurrentBacktest } =
    useBacktestStore();

  useThemeModeSync(themeMode);
  useDesktopLayoutSync(setDesktopLayout);

  const handleHorizontalLayout = useCallback(
    (layout: Layout) => {
      const dashboardSize = layout[0] ?? DEFAULT_DASHBOARD_PANEL_SIZE;
      setDashboardPanelSize(dashboardSize);
    },
    [setDashboardPanelSize],
  );

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

  const editorPanel = <EditorPanel code={strategyCode} onCodeChange={setStrategyCode} themeMode={themeMode} />;

  return (
    <div className="h-screen w-full bg-background text-foreground flex flex-col overflow-hidden">
      <AppHeader
        isRunning={isRunning}
        isCodeVisible={isCodeVisible}
        themeMode={themeMode}
        onRunBacktest={() => {
          void runCurrentBacktest();
        }}
        onOpenSettings={openSettings}
        onToggleCodeVisibility={toggleCodeVisibility}
        onToggleTheme={toggleThemeMode}
      />

      <main className="flex-1 overflow-hidden">
        <BacktestWorkspaceTemplate
          isDesktopLayout={isDesktopLayout}
          isCodeVisible={isCodeVisible}
          dashboardPanelSize={dashboardPanelSize}
          onHorizontalLayout={handleHorizontalLayout}
          dashboardPanel={dashboardPanel}
          editorPanel={editorPanel}
        />
      </main>

      <AIAssistantHud onApplyStrategyCode={setStrategyCode} />

      <BacktestSettingsPanel
        isOpen={isSettingsOpen}
        settings={settings}
        onSettingsChange={setSettings}
        onClose={closeSettings}
      />
    </div>
  );
}
