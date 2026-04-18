import { useCallback, useEffect, useMemo, useState } from "react";
import type { Layout } from "react-resizable-panels";

import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { runBacktest } from "@/features/backtest/api";
import { AIAssistantHud } from "@/features/backtest/components/AIAssistantHud";
import { AppHeader } from "@/features/backtest/components/AppHeader";
import { BacktestSettingsPanel } from "@/features/backtest/components/BacktestSettingsPanel";
import { DashboardPanel } from "@/features/backtest/components/DashboardPanel";
import { EditorPanel } from "@/features/backtest/components/EditorPanel";
import { defaultBacktestSettings, defaultStrategyCode } from "@/features/backtest/defaults";
import { formatKpiLabel, formatKpiValue } from "@/features/backtest/utils";
import type {
  BacktestRunResponse,
  BacktestRunStatus,
  EquityPoint,
  KpiMetric,
  KpiMetricTone,
  KpiRow,
  MarketOhlcvPoint,
  Trade,
} from "@/types/backtest";
import type { ThemeMode } from "@/types/theme";

interface SummaryKpiDefinition {
  key: string;
  label: string;
  description: string;
  icon: KpiMetric["icon"];
}

const SUMMARY_KPI_DEFINITIONS: SummaryKpiDefinition[] = [
  {
    key: "total_return_pct",
    label: "Total Return",
    description: "Strategy total return percentage",
    icon: "trending-up",
  },
  {
    key: "net_pnl",
    label: "Net PnL",
    description: "Net profit and loss after fees",
    icon: "activity",
  },
  {
    key: "max_drawdown_pct",
    label: "Max Drawdown",
    description: "Largest drawdown from equity peak",
    icon: "trending-down",
  },
  {
    key: "win_rate_pct",
    label: "Win Rate",
    description: "Percent of profitable trades",
    icon: "activity",
  },
  {
    key: "profit_factor",
    label: "Profit Factor",
    description: "Gross profit divided by gross loss",
    icon: "trending-up",
  },
  {
    key: "sharpe_ratio",
    label: "Sharpe Ratio",
    description: "Annualized return-to-volatility ratio",
    icon: "activity",
  },
];

const DEFAULT_DASHBOARD_PANEL_SIZE = 62;
const DESKTOP_LAYOUT_QUERY = "(min-width: 1024px)";
const THEME_STORAGE_KEY = "zstar.theme";
const EMPTY_EQUITY_DATA: EquityPoint[] = [];
const EMPTY_MARKET_OHLCV_DATA: MarketOhlcvPoint[] = [];
const EMPTY_TRADES: Trade[] = [];
const EMPTY_KPI_METRICS: KpiMetric[] = [];
const EMPTY_KPI_ROWS: KpiRow[] = [];

function getInitialThemeMode(): ThemeMode {
  if (globalThis.window === undefined) {
    return "dark";
  }

  try {
    const persistedTheme = globalThis.window.localStorage.getItem(THEME_STORAGE_KEY);
    return persistedTheme === "light" ? "light" : "dark";
  } catch {
    return "dark";
  }
}

function getInitialDesktopLayout(): boolean {
  if (globalThis.window === undefined) {
    return true;
  }

  return globalThis.window.matchMedia(DESKTOP_LAYOUT_QUERY).matches;
}

function getKpiTone(metricKey: string, value: number | string | null): KpiMetricTone {
  if (value === null || typeof value !== "number") {
    return "neutral";
  }

  if (metricKey === "max_drawdown_pct") {
    return value < -10 ? "negative" : "neutral";
  }

  if (metricKey === "win_rate_pct") {
    return value >= 50 ? "positive" : "negative";
  }

  if (metricKey === "profit_factor" || metricKey === "sharpe_ratio") {
    if (value > 1) return "positive";
    if (value < 0) return "negative";
    return "neutral";
  }
  
  if (value > 0) return "positive";
  if (value < 0) return "negative";
  return "neutral";
}

function mapSummaryKpis(payload: BacktestRunResponse | null): KpiMetric[] {
  if (!payload) {
    return [];
  }

  return SUMMARY_KPI_DEFINITIONS.map((definition) => {
    const metricValue = payload.kpis[definition.key] ?? null;
    return {
      id: definition.key,
      label: definition.label,
      value: formatKpiValue(definition.key, metricValue),
      description: definition.description,
      tone: getKpiTone(definition.key, metricValue),
      icon: definition.icon,
    };
  });
}

function mapKpiRows(payload: BacktestRunResponse | null): KpiRow[] {
  if (!payload) {
    return [];
  }

  return Object.entries(payload.kpis)
    .sort(([keyA], [keyB]) => keyA.localeCompare(keyB))
    .map(([key, value]) => ({
      key,
      label: formatKpiLabel(key),
      value: formatKpiValue(key, value),
    }));
}

export default function App() {
  const [isRunning, setIsRunning] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [settings, setSettings] = useState(defaultBacktestSettings);
  const [backtestResult, setBacktestResult] = useState<BacktestRunResponse | null>(null);
  const [runStatus, setRunStatus] = useState<BacktestRunStatus | null>(null);
  const [isCodeVisible, setIsCodeVisible] = useState(true);
  const [dashboardPanelSize, setDashboardPanelSize] = useState(DEFAULT_DASHBOARD_PANEL_SIZE);
  const [themeMode, setThemeMode] = useState<ThemeMode>(getInitialThemeMode);
  const [isDesktopLayout, setIsDesktopLayout] = useState(getInitialDesktopLayout);
  const [strategyCode, setStrategyCode] = useState(defaultStrategyCode);

  useEffect(() => {
    if (globalThis.window === undefined) {
      return;
    }

    const mediaQueryList = globalThis.window.matchMedia(DESKTOP_LAYOUT_QUERY);
    const handleChange = (event: MediaQueryListEvent) => {
      setIsDesktopLayout(event.matches);
    };

    setIsDesktopLayout(mediaQueryList.matches);
    mediaQueryList.addEventListener("change", handleChange);
    return () => {
      mediaQueryList.removeEventListener("change", handleChange);
    };
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove("dark", "light");
    root.classList.add(themeMode);

    try {
      globalThis.window.localStorage.setItem(THEME_STORAGE_KEY, themeMode);
    } catch {
      // Keep in-memory theme if storage is unavailable.
    }
  }, [themeMode]);

  const handleCodeChange = useCallback((nextCode: string) => {
    setStrategyCode(nextCode);
  }, []);

  const handleApplyStrategyCode = useCallback((nextCode: string) => {
    setStrategyCode(nextCode);
  }, []);

  const handleRunBacktest = useCallback(async () => {
    setIsRunning(true);
    setRunStatus(null);

    const slippageSeed = settings.slippageSeed.trim();
    const parsedSlippageSeed = slippageSeed ? Number(slippageSeed) : undefined;
    const slippageSeedPayload =
      parsedSlippageSeed !== undefined && Number.isFinite(parsedSlippageSeed)
        ? parsedSlippageSeed
        : undefined;

    try {
      const result = await runBacktest({
        strategy_code: strategyCode,
        data: {
          symbol: settings.symbol,
          start_date: settings.startDate,
          end_date: settings.endDate,
          interval: settings.interval

        },
        backtest_config: {
          initial_balance: settings.initialBalance,
          entry_fee_pct: settings.entryFeePct,
          exit_fee_pct: settings.exitFeePct,
          slippage_pct: settings.slippagePct,
          ...(slippageSeedPayload === undefined ? {} : { slippage_seed: slippageSeedPayload }),
        }
      });

      setBacktestResult(result);
      setRunStatus({
        tone: "success",
        message: "Backtest completed successfully.",
      });
    } catch (error) {
      setRunStatus({
        tone: "error",
        message: error instanceof Error ? error.message : "Backtest failed.",
      });
    } finally {
      setIsRunning(false);
    }
  }, [settings, strategyCode]);

  const handleToggleCodeVisibility = useCallback(() => {
    setIsCodeVisible((currentVisibility) => !currentVisibility);
  }, []);

  const handleHorizontalLayout = useCallback((layout: Layout) => {
    const dashboardSize = layout[0] ?? DEFAULT_DASHBOARD_PANEL_SIZE;
    setDashboardPanelSize(dashboardSize);
  }, []);

  const handleToggleTheme = useCallback(() => {
    setThemeMode((currentTheme) => (currentTheme === "dark" ? "light" : "dark"));
  }, []);

  const kpiMetrics = useMemo(
    () => (backtestResult ? mapSummaryKpis(backtestResult) : EMPTY_KPI_METRICS),
    [backtestResult],
  );
  const kpiRows = useMemo(
    () => (backtestResult ? mapKpiRows(backtestResult) : EMPTY_KPI_ROWS),
    [backtestResult],
  );
  const equityData = backtestResult?.equity_curve ?? EMPTY_EQUITY_DATA;
  const marketOhlcvData = backtestResult?.market_ohlcv ?? EMPTY_MARKET_OHLCV_DATA;
  const recentTrades = backtestResult?.trades ?? EMPTY_TRADES;

  const mainContent = (() => {
    if (isDesktopLayout) {
      if (isCodeVisible) {
        return (
          <div className="h-full">
            <ResizablePanelGroup direction="horizontal" onLayoutChange={handleHorizontalLayout}>
              <ResizablePanel defaultSize={dashboardPanelSize} minSize={24} className="flex flex-col">
                <DashboardPanel
                  equityData={equityData}
                  marketOhlcvData={marketOhlcvData}
                  kpiMetrics={kpiMetrics}
                  kpiRows={kpiRows}
                  recentTrades={recentTrades}
                  runStatus={runStatus}
                  settings={settings}
                />
              </ResizablePanel>

              <ResizableHandle />

              <ResizablePanel defaultSize={100 - dashboardPanelSize} minSize={22} className="border-l border-border/80">
                <EditorPanel code={strategyCode} onCodeChange={handleCodeChange} themeMode={themeMode} />
              </ResizablePanel>
            </ResizablePanelGroup>
          </div>
        );
      }

      return (
        <div className="h-full">
          <section className="h-full min-h-0 overflow-hidden flex flex-col">
            <DashboardPanel
              equityData={equityData}
              marketOhlcvData={marketOhlcvData}
              kpiMetrics={kpiMetrics}
              kpiRows={kpiRows}
              recentTrades={recentTrades}
              runStatus={runStatus}
              settings={settings}
            />
          </section>
        </div>
      );
    }

    if (isCodeVisible) {
      return (
        <div className="grid h-full grid-rows-[320px_minmax(0,1fr)]">
          <section className="min-h-0 border-b border-border/80">
            <EditorPanel code={strategyCode} onCodeChange={handleCodeChange} themeMode={themeMode} />
          </section>
          <section className="min-h-0 overflow-hidden flex flex-col">
            <DashboardPanel
              equityData={equityData}
              marketOhlcvData={marketOhlcvData}
              kpiMetrics={kpiMetrics}
              kpiRows={kpiRows}
              recentTrades={recentTrades}
              runStatus={runStatus}
              settings={settings}
            />
          </section>
        </div>
      );
    }

    return (
      <section className="h-full min-h-0 overflow-hidden flex flex-col">
        <DashboardPanel
          equityData={equityData}
          marketOhlcvData={marketOhlcvData}
          kpiMetrics={kpiMetrics}
          kpiRows={kpiRows}
          recentTrades={recentTrades}
          runStatus={runStatus}
          settings={settings}
        />
      </section>
    );
  })();

  return (
    <div className="h-screen w-full bg-background text-foreground flex flex-col overflow-hidden">
      <AppHeader
        isRunning={isRunning}
        isCodeVisible={isCodeVisible}
        themeMode={themeMode}
        onRunBacktest={handleRunBacktest}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onToggleCodeVisibility={handleToggleCodeVisibility}
        onToggleTheme={handleToggleTheme}
      />

      <main className="flex-1 overflow-hidden">{mainContent}</main>

      <AIAssistantHud onApplyStrategyCode={handleApplyStrategyCode} />

      <BacktestSettingsPanel
        isOpen={isSettingsOpen}
        settings={settings}
        onSettingsChange={setSettings}
        onClose={() => setIsSettingsOpen(false)}
      />
    </div>
  );
}
