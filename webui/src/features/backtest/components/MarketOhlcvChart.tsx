import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Maximize2, Minimize2, Minus, Plus, RotateCcw } from "lucide-react";
import { useScrollLock } from "@/hooks/useScrollLock";
import {
  ColorType,
  createChart,
  type CandlestickData,
  type HistogramData,
  type IChartApi,
  type UTCTimestamp,
} from "lightweight-charts";

import { Button } from "@/components/ui/button";
import { SECTION_TITLE_CLASS_NAME } from "@/features/backtest/constants";
import { cn } from "@/lib/utils";
import type { MarketOhlcvPoint, Trade } from "@/types/backtest";

const DEFAULT_BAR_SPACING = 8;
const MIN_BAR_SPACING = 2;
const MAX_BAR_SPACING = 48;

interface MarketOhlcvChartProps {
  readonly data: MarketOhlcvPoint[];
  readonly trades: Trade[];
}

interface PreparedMarketData {
  readonly candles: CandlestickData[];
  readonly volumes: HistogramData[];
}

function parseTimestamp(value: string): UTCTimestamp | null {
  const milliseconds = new Date(value).getTime();
  if (!Number.isFinite(milliseconds)) {
    return null;
  }

  return Math.floor(milliseconds / 1000) as UTCTimestamp;
}

function isValidNumber(value: number | null): value is number {
  return value !== null && Number.isFinite(value);
}

function prepareMarketData(data: MarketOhlcvPoint[]): PreparedMarketData {
  const sortedData = [...data].sort(
    (a, b) => new Date(a.datetime).getTime() - new Date(b.datetime).getTime(),
  );

  const candles: CandlestickData[] = [];
  const volumes: HistogramData[] = [];
  let lastTime: number | null = null;

  for (const point of sortedData) {
    const time = parseTimestamp(point.datetime);
    if (time === null) {
      continue;
    }

    const numericTime = Number(time);
    if (numericTime === lastTime) {
      continue;
    }

    if (
      !isValidNumber(point.open) ||
      !isValidNumber(point.high) ||
      !isValidNumber(point.low) ||
      !isValidNumber(point.close)
    ) {
      continue;
    }

    candles.push({
      time,
      open: point.open,
      high: point.high,
      low: point.low,
      close: point.close,
    });

    if (isValidNumber(point.volume)) {
      volumes.push({
        time,
        value: point.volume,
        color: point.close >= point.open ? "#22c55e66" : "#ef444466",
      });
    }

    lastTime = numericTime;
  }

  return { candles, volumes };
}

function buildTradeMarkers(trades: Trade[]) {
  const markers = trades.flatMap((trade) => {
    const entryTime = parseTimestamp(trade.entry_datetime);
    const exitTime = parseTimestamp(trade.exit_datetime);
    const isLong = trade.side === "LONG";

    return [
      entryTime === null
        ? null
        : {
            time: entryTime,
            position: isLong ? "belowBar" : "aboveBar",
            color: isLong ? "#22c55e" : "#ef4444",
            shape: isLong ? "arrowUp" : "arrowDown",
            text: isLong ? "Long entry" : "Short entry",
          },
      exitTime === null
        ? null
        : {
            time: exitTime,
            position: "inBar",
            color: "#f59e0b",
            shape: "circle",
            text: "Exit",
          },
    ];
  });

  return markers
    .filter((marker): marker is NonNullable<(typeof markers)[number]> => marker !== null)
    .sort((a, b) => Number(a.time) - Number(b.time));
}

export function MarketOhlcvChart({ data, trades }: MarketOhlcvChartProps) {
  const inlineContainerRef = useRef<HTMLDivElement | null>(null);
  const expandedContainerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<any>(null);
  const volumeSeriesRef = useRef<any>(null);
  const [barSpacing, setBarSpacing] = useState(DEFAULT_BAR_SPACING);
  const [chartInitError, setChartInitError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  const preparedData = useMemo(() => prepareMarketData(data), [data]);
  const tradeMarkers = useMemo(() => buildTradeMarkers(trades), [trades]);

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

  useLayoutEffect(() => {
    const container = isExpanded ? expandedContainerRef.current : inlineContainerRef.current;
    if (!container) {
      return;
    }

    chartRef.current?.remove();
    chartRef.current = null;
    candlestickSeriesRef.current = null;
    volumeSeriesRef.current = null;

    let cleanupResize: (() => void) | null = null;
    let animationFrameA: number | null = null;
    let animationFrameB: number | null = null;

    try {
      const initialRect = container.getBoundingClientRect();
      const chart = createChart(container, {
        width: Math.max(initialRect.width || container.clientWidth, 320),
        height: Math.max(initialRect.height || container.clientHeight, 320),
        layout: {
          background: { type: ColorType.Solid, color: "rgba(0,0,0,0)" },
          textColor: "rgb(161,161,170)",
        },
        grid: {
          vertLines: { color: "rgba(63,63,70,0.35)" },
          horzLines: { color: "rgba(63,63,70,0.35)" },
        },
        crosshair: {
          vertLine: { color: "rgba(161,161,170,0.65)" },
          horzLine: { color: "rgba(161,161,170,0.65)" },
        },
        rightPriceScale: {
          borderColor: "rgba(63,63,70,1)",
        },
        timeScale: {
          borderColor: "rgba(63,63,70,1)",
          barSpacing: DEFAULT_BAR_SPACING,
          rightOffset: 2,
          timeVisible: true,
        },
        handleScroll: true,
        handleScale: true,
      });

      const candlestickSeries = chart.addCandlestickSeries({
        upColor: "#22c55e",
        downColor: "#ef4444",
        borderVisible: false,
        wickUpColor: "#22c55e",
        wickDownColor: "#ef4444",
      });

      const volumeSeries = chart.addHistogramSeries({
        priceScaleId: "volume",
        priceFormat: {
          type: "volume",
        },
      });
      volumeSeries.priceScale().applyOptions({
        scaleMargins: { top: 0.72, bottom: 0 },
        borderVisible: false,
      });

      chartRef.current = chart;
      candlestickSeriesRef.current = candlestickSeries;
      volumeSeriesRef.current = volumeSeries;

      candlestickSeries.setData(preparedData.candles);
      volumeSeries.setData(preparedData.volumes);
      candlestickSeries.setMarkers?.(tradeMarkers as any);
      chart.timeScale().applyOptions({ barSpacing });
      if (preparedData.candles.length > 0) {
        chart.timeScale().fitContent();
      }

      setChartInitError(null);

      const applyCurrentSize = () => {
        const rect = container.getBoundingClientRect();
        chart.applyOptions({
          width: Math.max(rect.width || container.clientWidth, 320),
          height: Math.max(rect.height || container.clientHeight, 320),
        });
      };

      animationFrameA = requestAnimationFrame(() => {
        applyCurrentSize();
        animationFrameB = requestAnimationFrame(() => {
          applyCurrentSize();
          if (preparedData.candles.length > 0) {
            chart.timeScale().fitContent();
          }
        });
      });

      if (typeof ResizeObserver === "undefined") {
        const handleWindowResize = () => {
          applyCurrentSize();
        };
        globalThis.window.addEventListener("resize", handleWindowResize);
        cleanupResize = () => globalThis.window.removeEventListener("resize", handleWindowResize);
      } else {
        const resizeObserver = new ResizeObserver((entries) => {
          const entry = entries[0];
          if (!entry) {
            return;
          }

          const width = Math.max(entry.contentRect.width || container.clientWidth, 320);
          const height = Math.max(entry.contentRect.height || container.clientHeight, 320);
          chart.applyOptions({ width, height });
        });
        resizeObserver.observe(container);
        cleanupResize = () => resizeObserver.disconnect();
      }
    } catch {
      setChartInitError("Unable to initialize market chart.");
    }

    return () => {
      if (animationFrameA !== null) {
        cancelAnimationFrame(animationFrameA);
      }
      if (animationFrameB !== null) {
        cancelAnimationFrame(animationFrameB);
      }
      cleanupResize?.();
      chartRef.current?.remove();
      chartRef.current = null;
      candlestickSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, [isExpanded]);

  useEffect(() => {
    const chart = chartRef.current;
    const candlestickSeries = candlestickSeriesRef.current;
    const volumeSeries = volumeSeriesRef.current;
    if (!chart || !candlestickSeries || !volumeSeries) {
      return;
    }

    try {
      candlestickSeries.setData(preparedData.candles);
      volumeSeries.setData(preparedData.volumes);
      candlestickSeries.setMarkers?.(tradeMarkers as any);

      if (preparedData.candles.length > 0) {
        chart.timeScale().fitContent();
      }
      setChartInitError(null);
    } catch {
      setChartInitError("Unable to render market chart data.");
    }
  }, [preparedData, tradeMarkers]);

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) {
      return;
    }

    chart.timeScale().applyOptions({ barSpacing });
  }, [barSpacing]);

  const chartControls = (
    <div className="flex items-center gap-2">
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="h-9 w-9 border border-border/80 bg-muted/60 text-foreground hover:bg-muted"
        aria-label="Zoom out"
        title="Zoom out"
        onClick={() =>
          setBarSpacing((currentSpacing) => Math.max(MIN_BAR_SPACING, Math.floor(currentSpacing / 1.2)))
        }
        disabled={preparedData.candles.length === 0}
      >
        <Minus className="h-4 w-4" />
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="h-9 w-9 border border-border/80 bg-muted/60 text-foreground hover:bg-muted"
        aria-label="Zoom in"
        title="Zoom in"
        onClick={() =>
          setBarSpacing((currentSpacing) => Math.min(MAX_BAR_SPACING, Math.ceil(currentSpacing * 1.2)))
        }
        disabled={preparedData.candles.length === 0}
      >
        <Plus className="h-4 w-4" />
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="h-9 w-9 border border-border/80 bg-muted/60 text-foreground hover:bg-muted"
        aria-label="Reset zoom"
        title="Reset zoom"
        onClick={() => {
          setBarSpacing(DEFAULT_BAR_SPACING);
          chartRef.current?.timeScale().fitContent();
        }}
        disabled={preparedData.candles.length === 0}
      >
        <RotateCcw className="h-4 w-4" />
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

  const chartSection = (
    <section
      className={cn(
        isExpanded
          ? "fixed inset-5 z-[40010] flex min-h-0 flex-col rounded-2xl border border-border/80 bg-background/95 p-6 shadow-2xl backdrop-blur-sm dark:bg-[#070b14]/95"
          : "relative border-b border-border/80 px-2 pb-10 pt-2 sm:px-4 lg:px-6",
      )}
    >
      <div className={cn("mb-5 flex items-center justify-between gap-3", isExpanded ? "shrink-0" : "")}>
        <h3 className={SECTION_TITLE_CLASS_NAME}>Executed Trades in Market</h3>
        {chartControls}
      </div>

      {chartInitError ? <p className="mb-3 text-sm text-red-300">{chartInitError}</p> : null}
      {preparedData.candles.length === 0 ? (
        <p className="mb-3 text-sm text-muted-foreground">
          Run a backtest to display market OHLCV candles and trade markers.
        </p>
      ) : null}
      <div
        ref={isExpanded ? expandedContainerRef : inlineContainerRef}
        className={cn("w-full", isExpanded ? "min-h-[420px] flex-1" : "h-[440px]")}
      />
    </section>
  );

  if (isExpanded && typeof document !== "undefined") {
    return createPortal(
      <>
        <button
          type="button"
          aria-label="Close expanded chart"
          className="fixed inset-0 z-[40000] cursor-default border-0 bg-black/70 p-0 backdrop-blur-[1.5px]"
          onClick={() => setIsExpanded(false)}
        />
        {chartSection}
      </>,
      document.body,
    );
  }

  return chartSection;
}
