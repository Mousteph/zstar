"use client";

import { useCallback, useMemo, useState } from "react";

import { AppHeader } from "@/components/organisms/backtest/AppHeader";
import { BacktestSettingsPanel } from "@/components/organisms/backtest/BacktestSettingsPanel";
import { DashboardPanel } from "@/components/organisms/backtest/DashboardPanel";
import { fetchStrategies } from "@/features/backtest/api";
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
  const [selectedStrategy, setSelectedStrategy] = useState("default_strategy");
  const [strategyOptions, setStrategyOptions] = useState<string[]>([]);
  const [isStrategyMenuOpen, setIsStrategyMenuOpen] = useState(false);
  const [isStrategiesLoading, setIsStrategiesLoading] = useState(false);
  const [strategiesError, setStrategiesError] = useState<string | null>(null);

  const {
    isSettingsOpen,
    themeMode,
    openSettings,
    closeSettings,
    toggleThemeMode,
  } = useUIStore();

  const {
    isRunning,
    isValidating,
    csvFiles,
    csvFilesError,
    isCsvFilesLoading,
    isCsvUploading,
    settings,
    backtestResult,
    runStatus,
    validationResult,
    setSettings,
    loadCsvFiles,
    uploadCsv,
    runValidation,
    runCurrentBacktest,
  } = useBacktestStore();

  useThemeModeSync(themeMode);

  const kpiMetrics = useMemo(() => (backtestResult ? mapSummaryKpis(backtestResult) : EMPTY_KPI_METRICS), [backtestResult]);
  const kpiRows = useMemo(() => (backtestResult ? mapKpiRows(backtestResult) : EMPTY_KPI_ROWS), [backtestResult]);
  const equityData = backtestResult?.equity_curve ?? EMPTY_EQUITY_DATA;
  const marketOhlcvData = backtestResult?.market_ohlcv ?? EMPTY_MARKET_OHLCV_DATA;
  const recentTrades = backtestResult?.trades ?? EMPTY_TRADES;

  const closeStrategyMenu = useCallback(() => {
    setIsStrategyMenuOpen(false);
  }, []);

  const toggleStrategyMenu = useCallback(() => {
    if (isStrategyMenuOpen) {
      setIsStrategyMenuOpen(false);
      return;
    }

    setIsStrategyMenuOpen(true);
    setIsStrategiesLoading(true);
    setStrategiesError(null);

    void fetchStrategies()
      .then((strategies) => {
        setStrategyOptions(strategies);
      })
      .catch((error: unknown) => {
        setStrategiesError(error instanceof Error ? error.message : "Unable to fetch strategies.");
      })
      .finally(() => {
        setIsStrategiesLoading(false);
      });
  }, [isStrategyMenuOpen]);

  const dashboardPanel = (
    <DashboardPanel
      equityData={equityData}
      marketOhlcvData={marketOhlcvData}
      kpiMetrics={kpiMetrics}
      kpiRows={kpiRows}
      recentTrades={recentTrades}
      runStatus={runStatus}
      validationResult={validationResult}
      isValidating={isValidating}
      backtestResult={backtestResult}
      selectedStrategy={selectedStrategy}
      settings={settings}
      themeMode={themeMode}
    />
  );

  return (
    <div className="h-screen w-full bg-background text-foreground flex flex-col overflow-hidden">
      {isStrategyMenuOpen ? (
        <button
          type="button"
          className="fixed inset-0 z-[12000] bg-black/50 backdrop-blur-[2px]"
          onClick={closeStrategyMenu}
          aria-label="Close strategy selector"
        />
      ) : null}

      <AppHeader
        isRunning={isRunning}
        isValidating={isValidating}
        selectedStrategy={selectedStrategy}
        strategyOptions={strategyOptions}
        isStrategyMenuOpen={isStrategyMenuOpen}
        isStrategiesLoading={isStrategiesLoading}
        strategiesError={strategiesError}
        themeMode={themeMode}
        onRunBacktest={() => {
          void runCurrentBacktest(selectedStrategy);
        }}
        onCheckCode={() => {
          void runValidation(selectedStrategy);
        }}
        onOpenSettings={openSettings}
        onToggleTheme={toggleThemeMode}
        onToggleStrategyMenu={toggleStrategyMenu}
        onSelectStrategy={(strategy) => {
          setSelectedStrategy(strategy);
          setIsStrategyMenuOpen(false);
        }}
        onCloseStrategyMenu={closeStrategyMenu}
      />

      <main className="flex-1 overflow-hidden">{dashboardPanel}</main>

      <BacktestSettingsPanel
        isOpen={isSettingsOpen}
        settings={settings}
        csvFiles={csvFiles}
        csvFilesError={csvFilesError}
        isCsvFilesLoading={isCsvFilesLoading}
        isCsvUploading={isCsvUploading}
        onSettingsChange={setSettings}
        onLoadCsvFiles={loadCsvFiles}
        onUploadCsv={uploadCsv}
        onClose={closeSettings}
      />
    </div>
  );
}
