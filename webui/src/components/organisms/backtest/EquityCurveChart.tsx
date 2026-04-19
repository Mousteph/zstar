"use client";

import { useEffect, useMemo, useState } from "react";
import { Eye, EyeOff, Maximize2, Minimize2 } from "lucide-react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

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

function formatAxisValue(value: number): string {
  if (!Number.isFinite(value)) {
    return "0";
  }

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2,
  }).format(value);
}

export function EquityCurveChart({ data }: Readonly<EquityCurveChartProps>) {
  const [isBuyAndHoldVisible, setIsBuyAndHoldVisible] = useState(true);
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
      tooltipShadow: readCssVariable("--chart-tooltip-shadow", "0 4px 12px rgba(0,0,0,0.5)"),
    }),
    [isExpanded],
  );

  const chartControls = (
    <div className="flex items-center gap-2">
      <ActionIconButton
        type="button"
        onClick={() => setIsBuyAndHoldVisible((currentVisibility) => !currentVisibility)}
        aria-label={isBuyAndHoldVisible ? "Hide Buy & Hold" : "Show Buy & Hold"}
        title={isBuyAndHoldVisible ? "Hide Buy & Hold" : "Show Buy & Hold"}
      >
        {isBuyAndHoldVisible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </ActionIconButton>

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
    <div className={cn("w-full", isExpanded ? "min-h-[360px] flex-1" : "h-[360px] sm:h-[400px]")}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 28, left: 14, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" opacity={0.32} />
          <XAxis
            dataKey="datetime"
            stroke="hsl(var(--muted-foreground))"
            fontSize={12}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => formatDateTime(value).split(",")[0]}
            minTickGap={40}
          />
          <YAxis
            stroke="hsl(var(--muted-foreground))"
            fontSize={12}
            tickLine={false}
            axisLine={false}
            width={96}
            tickFormatter={(value) => formatAxisValue(Number(value))}
            domain={["auto", "auto"]}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(var(--card))",
              borderColor: "hsl(var(--border))",
              borderRadius: "8px",
              color: "hsl(var(--foreground))",
              boxShadow: chartColors.tooltipShadow,
            }}
            itemStyle={{ color: chartColors.strategyStroke }}
            formatter={(value, name) => [formatCurrency(Number(value)), name]}
            labelFormatter={(value) => formatDateTime(String(value))}
            labelStyle={{ color: "hsl(var(--muted-foreground))", marginBottom: "4px" }}
            cursor={{
              stroke: "hsl(var(--muted-foreground))",
              strokeWidth: 1,
              strokeDasharray: "4 4",
            }}
          />
          <Legend wrapperStyle={{ paddingTop: "10px" }} />
          <Line
            type="monotone"
            name="Strategy"
            dataKey="strategy"
            stroke={chartColors.strategyStroke}
            strokeWidth={3}
            dot={false}
            className="equity-strategy-line"
          />
          {isBuyAndHoldVisible ? (
            <Line
              type="monotone"
              name="Buy & Hold"
              dataKey="buy_and_hold"
              stroke={chartColors.buyHoldStroke}
              strokeWidth={2}
              dot={false}
            />
          ) : null}
        </LineChart>
      </ResponsiveContainer>
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
