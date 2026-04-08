import { useEffect, useState } from "react";
import { useScrollLock } from "@/hooks/useScrollLock";
import { createPortal } from "react-dom";
import { Eye, EyeOff, Maximize2, Minimize2 } from "lucide-react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Button } from "@/components/ui/button";
import { SECTION_TITLE_CLASS_NAME } from "@/features/backtest/constants";
import { formatCurrency, formatDateTime } from "@/features/backtest/utils";
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

export function EquityCurveChart({ data }: EquityCurveChartProps) {
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

  const chartControls = (
    <div className="flex items-center gap-2">
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="h-9 w-9 border border-border/80 bg-muted/60 text-foreground hover:bg-muted"
        onClick={() => setIsBuyAndHoldVisible((currentVisibility) => !currentVisibility)}
        aria-label={isBuyAndHoldVisible ? "Hide Buy & Hold" : "Show Buy & Hold"}
        title={isBuyAndHoldVisible ? "Hide Buy & Hold" : "Show Buy & Hold"}
      >
        {isBuyAndHoldVisible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="h-9 w-9 border border-border/80 bg-muted/60 text-foreground hover:bg-muted"
        onClick={() => setIsExpanded((currentState) => !currentState)}
        aria-label={isExpanded ? "Minimize chart" : "Expand chart"}
        title={isExpanded ? "Minimize chart" : "Expand chart"}
      >
        {isExpanded ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
      </Button>
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
              boxShadow: "0 4px 12px rgba(0,0,0,0.5)",
            }}
            itemStyle={{ color: "#10b981" }}
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
            stroke="#10b981"
            strokeWidth={3}
            dot={false}
            style={{ filter: "drop-shadow(0 0 8px rgba(16, 185, 129, 0.45))" }}
          />
          {isBuyAndHoldVisible ? (
            <Line
              type="monotone"
              name="Buy & Hold"
              dataKey="buy_and_hold"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
            />
          ) : null}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );

  const chartSection = (
    <section
      className={cn(
        isExpanded
          ? "fixed inset-5 z-[40010] flex flex-col rounded-2xl border border-border/80 bg-background/95 p-6 shadow-2xl backdrop-blur-sm dark:bg-[#070b14]/95"
          : "relative border-b border-border/80 px-2 pb-9 pt-2 sm:px-4 lg:px-6",
      )}
    >
      <div className={cn("mb-5 flex items-center justify-between gap-3", isExpanded ? "shrink-0" : "")}>
        <h3 className={SECTION_TITLE_CLASS_NAME}>Equity Curve</h3>
        {chartControls}
      </div>
      {chartBody}
    </section>
  );

  if (isExpanded && typeof document !== "undefined") {
    return createPortal(
      <>
        <button
          type="button"
          className="fixed inset-0 z-[40000] bg-black/70 backdrop-blur-[1.5px]"
          onClick={() => setIsExpanded(false)}
          aria-label="Close expanded chart"
        />
        {chartSection}
      </>,
      document.body,
    );
  }

  return chartSection;
}
