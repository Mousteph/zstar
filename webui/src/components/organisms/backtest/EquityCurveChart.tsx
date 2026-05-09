"use client";

import { useEffect, useMemo, useState } from "react";
import { Maximize2, Minimize2 } from "lucide-react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { ActionIconButton } from "@/components/molecules/ActionIconButton";
import { ExpandableSection } from "@/components/molecules/ExpandableSection";
import { formatCurrency, formatDateTime } from "@/features/backtest/utils";
import { useScrollLock } from "@/hooks/useScrollLock";
import { readCssVariable } from "@/lib/dom/readCssVariable";
import { cn } from "@/lib/utils";
import type { EquityPoint } from "@/types/backtest";

interface EquityCurveChartProps {
  readonly data: EquityPoint[];
}

type EquitySeriesKey = "strategy" | "buy_and_hold" | "drawdown";

interface EquityChartPoint extends EquityPoint {
  readonly drawdown: number | null;
}

interface LegendSeriesConfig {
  readonly key: EquitySeriesKey;
  readonly label: string;
  readonly color: string;
}

function formatAxisValue(value: number): string {
  if (!Number.isFinite(value)) {
    return "0";
  }

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2,
  }).format(value);
}

function formatDrawdownValue(value: number): string {
  if (!Number.isFinite(value)) {
    return "0.00%";
  }

  return `${value.toFixed(2)}%`;
}

function buildEquityChartData(data: EquityPoint[]): EquityChartPoint[] {
  let peak: number | null = null;

  return data.map((point) => {
    if (point.strategy === null || !Number.isFinite(point.strategy) || point.strategy <= 0) {
      return { ...point, drawdown: null };
    }

    peak = peak === null ? point.strategy : Math.max(peak, point.strategy);
    const drawdown = peak > 0 ? (point.strategy / peak - 1) * 100 : null;

    return { ...point, drawdown };
  });
}

export function EquityCurveChart({ data }: Readonly<EquityCurveChartProps>) {
  const [visibleSeries, setVisibleSeries] = useState<Record<EquitySeriesKey, boolean>>({
    strategy: true,
    buy_and_hold: true,
    drawdown: true,
  });
  const [isExpanded, setIsExpanded] = useState(false);

  useScrollLock(isExpanded);

  useEffect(() => {
    if (!isExpanded) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsExpanded(false);
      }
    };

    globalThis.window.addEventListener("keydown", handleKeyDown);
    return () => {
      globalThis.window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isExpanded]);

  const chartColors = useMemo(
    () => ({
      strategyStroke: readCssVariable("--chart-positive", "rgb(16,185,129)"),
      buyHoldStroke: readCssVariable("--chart-neutral", "rgb(59,130,246)"),
      drawdownStroke: readCssVariable("--chart-negative", "rgb(244,63,94)"),
      tooltipShadow: readCssVariable("--chart-tooltip-shadow", "0 4px 12px rgba(0,0,0,0.5)"),
    }),
    [isExpanded],
  );

  const chartData = useMemo(() => buildEquityChartData(data), [data]);
  const legendSeries = useMemo<LegendSeriesConfig[]>(
    () => [
      { key: "buy_and_hold", label: "Buy & Hold", color: chartColors.buyHoldStroke },
      { key: "strategy", label: "Strategy", color: chartColors.strategyStroke },
      { key: "drawdown", label: "Drawdown", color: chartColors.drawdownStroke },
    ],
    [chartColors],
  );

  const toggleSeries = (seriesKey: EquitySeriesKey) => {
    setVisibleSeries((currentVisibility) => ({
      ...currentVisibility,
      [seriesKey]: !currentVisibility[seriesKey],
    }));
  };

  const chartControls = (
    <div className="flex items-center gap-2">
      <ActionIconButton
        type="button"
        onClick={() => setIsExpanded((currentState) => !currentState)}
        aria-label={isExpanded ? "Minimize chart" : "Expand chart"}
        title={isExpanded ? "Minimize chart" : "Expand chart"}
      >
        {isExpanded ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
      </ActionIconButton>
    </div>
  );

  const chartBody = data.length === 0 ? (
    <p className="text-sm text-muted-foreground">Run a backtest to display the equity curve.</p>
  ) : (
    <div className={cn("flex w-full flex-col pb-5", isExpanded ? "min-h-[360px] flex-1" : "h-[380px] sm:h-[420px]")}>
      <div className="min-h-0 flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 8, right: 34, left: 14, bottom: 24 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" opacity={0.32} />
          <XAxis
            dataKey="datetime"
            stroke="hsl(var(--muted-foreground))"
            fontSize={12}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => formatDateTime(value).split(",")[0]}
            minTickGap={40}
            tickMargin={16}
          />
          <YAxis
            stroke="hsl(var(--muted-foreground))"
            fontSize={12}
            tickLine={false}
            axisLine={false}
            width={96}
            tickFormatter={(value) => formatAxisValue(Number(value))}
            domain={["auto", "auto"]}
            yAxisId="equity"
          />
          {visibleSeries.drawdown ? (
            <YAxis
              yAxisId="drawdown"
              orientation="right"
              stroke={chartColors.drawdownStroke}
              fontSize={12}
              tickLine={false}
              axisLine={false}
              width={52}
              tickFormatter={(value) => formatDrawdownValue(Number(value))}
              domain={["dataMin", 0]}
              opacity={0.45}
            />
          ) : null}
          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(var(--card))",
              borderColor: "hsl(var(--border))",
              borderRadius: "8px",
              color: "hsl(var(--foreground))",
              boxShadow: chartColors.tooltipShadow,
            }}
            formatter={(value, name) => [
              name === "Drawdown" ? formatDrawdownValue(Number(value)) : formatCurrency(Number(value)),
              name,
            ]}
            labelFormatter={(value) => formatDateTime(String(value))}
            labelStyle={{ color: "hsl(var(--muted-foreground))", marginBottom: "4px" }}
            cursor={{
              stroke: "hsl(var(--muted-foreground))",
              strokeWidth: 1,
              strokeDasharray: "4 4",
            }}
          />
          {visibleSeries.strategy ? (
            <Line
              yAxisId="equity"
              type="monotone"
              name="Strategy"
              dataKey="strategy"
              stroke={chartColors.strategyStroke}
              strokeWidth={3}
              dot={false}
              className="equity-strategy-line"
            />
          ) : null}
          {visibleSeries.buy_and_hold ? (
            <Line
              yAxisId="equity"
              type="monotone"
              name="Buy & Hold"
              dataKey="buy_and_hold"
              stroke={chartColors.buyHoldStroke}
              strokeWidth={2}
              dot={false}
            />
          ) : null}
          {visibleSeries.drawdown ? (
            <Line
              yAxisId="drawdown"
              type="monotone"
              name="Drawdown"
              dataKey="drawdown"
              stroke={chartColors.drawdownStroke}
              strokeWidth={2}
              strokeOpacity={0.34}
              dot={false}
              connectNulls={false}
            />
          ) : null}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2 flex flex-wrap items-center justify-center gap-4">
        {legendSeries.map((series) => {
          const isVisible = visibleSeries[series.key];

          return (
            <button
              key={series.key}
              type="button"
              className={cn(
                "inline-flex items-center gap-2 rounded-md px-2 py-1 text-sm font-semibold transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                isVisible ? "opacity-100" : "opacity-35",
              )}
              style={{ color: series.color }}
              onClick={() => toggleSeries(series.key)}
              aria-pressed={isVisible}
              title={isVisible ? `Hide ${series.label}` : `Show ${series.label}`}
            >
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: series.color }} />
              {series.label}
            </button>
          );
        })}
      </div>
    </div>
  );

  return (
    <ExpandableSection
      isExpanded={isExpanded}
      onCollapse={() => setIsExpanded(false)}
      title="Equity Curve"
      controls={chartControls}
      inlineClassName="pb-9"
      expandedClassName="chart-expanded-surface"
    >
      {chartBody}
    </ExpandableSection>
  );
}
