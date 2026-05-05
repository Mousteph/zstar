"use client";

import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { Maximize2, Minimize2, Minus, Plus, RotateCcw } from "lucide-react";
import {
  ColorType,
  createChart,
  type BarData,
  type CandlestickData,
  type HistogramData,
  type IChartApi,
  type MouseEventParams,
  type SeriesMarker,
  type Time,
  type UTCTimestamp,
} from "lightweight-charts";

import { ActionIconButton } from "@/components/molecules/ActionIconButton";
import { ExpandableSection } from "@/components/molecules/ExpandableSection";
import { formatCurrency, formatDateTime, formatNumber } from "@/features/backtest/utils";
import { useScrollLock } from "@/hooks/useScrollLock";
import { readCssVariable } from "@/lib/dom/readCssVariable";
import { cn } from "@/lib/utils";
import type { MarketOhlcvPoint, Trade } from "@/types/backtest";
import type { ThemeMode } from "@/types/theme";

const DEFAULT_BAR_SPACING = 8;
const MIN_BAR_SPACING = 2;
const MAX_BAR_SPACING = 48;

type CandlestickSeriesApi = ReturnType<IChartApi["addCandlestickSeries"]>;
type HistogramSeriesApi = ReturnType<IChartApi["addHistogramSeries"]>;

interface MarketOhlcvChartProps {
  readonly data: MarketOhlcvPoint[];
  readonly trades: Trade[];
  readonly themeMode: ThemeMode;
}

interface PreparedMarketData {
  readonly candles: CandlestickData[];
  readonly volumes: HistogramData[];
  readonly volumeByTime: Map<number, number>;
}

interface TradeEvent {
  readonly type: "entry" | "exit";
  readonly trade: Trade;
}

interface CandleTooltipState {
  readonly left: number;
  readonly top: number;
  readonly candle: CandlestickData;
  readonly volume: number | null;
  readonly tradeEvents: TradeEvent[];
}

interface ChartPalette {
  readonly textColor: string;
  readonly gridColor: string;
  readonly crosshairColor: string;
  readonly borderColor: string;
  readonly upColor: string;
  readonly downColor: string;
  readonly exitColor: string;
  readonly volumeUpColor: string;
  readonly volumeDownColor: string;
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

function getChartPalette(): ChartPalette {
  return {
    textColor: readCssVariable("--chart-axis", "rgb(161,161,170)"),
    gridColor: readCssVariable("--chart-grid", "rgba(63,63,70,0.35)"),
    crosshairColor: readCssVariable("--chart-crosshair", "rgba(161,161,170,0.65)"),
    borderColor: readCssVariable("--chart-border", "rgba(63,63,70,1)"),
    upColor: readCssVariable("--chart-candle-up", "rgb(34,197,94)"),
    downColor: readCssVariable("--chart-candle-down", "rgb(239,68,68)"),
    exitColor: readCssVariable("--chart-exit", "rgb(245,158,11)"),
    volumeUpColor: readCssVariable("--chart-volume-up", "rgba(34,197,94,0.4)"),
    volumeDownColor: readCssVariable("--chart-volume-down", "rgba(239,68,68,0.4)"),
  };
}

function prepareMarketData(data: MarketOhlcvPoint[], palette: ChartPalette): PreparedMarketData {
  const sortedData = [...data].sort((a, b) => new Date(a.datetime).getTime() - new Date(b.datetime).getTime());

  const candles: CandlestickData[] = [];
  const volumes: HistogramData[] = [];
  const volumeByTime = new Map<number, number>();
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
        color: point.close >= point.open ? palette.volumeUpColor : palette.volumeDownColor,
      });
      volumeByTime.set(numericTime, point.volume);
    }

    lastTime = numericTime;
  }

  return { candles, volumes, volumeByTime };
}

function buildTradeEventsByTime(trades: Trade[]): Map<number, TradeEvent[]> {
  const eventsByTime = new Map<number, TradeEvent[]>();

  for (const trade of trades) {
    const entryTime = parseTimestamp(trade.entry_datetime);
    const exitTime = parseTimestamp(trade.exit_datetime);

    if (entryTime !== null) {
      const numericEntryTime = Number(entryTime);
      eventsByTime.set(numericEntryTime, [
        ...(eventsByTime.get(numericEntryTime) ?? []),
        { type: "entry", trade },
      ]);
    }

    if (exitTime !== null) {
      const numericExitTime = Number(exitTime);
      eventsByTime.set(numericExitTime, [
        ...(eventsByTime.get(numericExitTime) ?? []),
        { type: "exit", trade },
      ]);
    }
  }

  return eventsByTime;
}

function buildTradeMarkers(trades: Trade[], palette: ChartPalette): SeriesMarker<Time>[] {
  const markers = trades.flatMap((trade) => {
    const entryTime = parseTimestamp(trade.entry_datetime);
    const exitTime = parseTimestamp(trade.exit_datetime);
    const isLong = trade.side === "LONG";

    const entryMarker: SeriesMarker<Time> | null =
      entryTime === null
        ? null
        : {
            time: entryTime,
            position: isLong ? "belowBar" : "aboveBar",
            color: isLong ? palette.upColor : palette.downColor,
            shape: isLong ? "arrowUp" : "arrowDown",
            text: isLong ? "Long entry" : "Short entry",
          };

    const exitMarker: SeriesMarker<Time> | null =
      exitTime === null
        ? null
        : {
            time: exitTime,
            position: "inBar",
            color: palette.exitColor,
            shape: "circle",
            text: "Exit",
          };

    return [
      entryMarker,
      exitMarker,
    ];
  });

  return markers
    .filter((marker): marker is NonNullable<(typeof markers)[number]> => marker !== null)
    .sort((a, b) => Number(a.time) - Number(b.time));
}

export function MarketOhlcvChart({ data, trades, themeMode }: Readonly<MarketOhlcvChartProps>) {
  const inlineContainerRef = useRef<HTMLDivElement | null>(null);
  const expandedContainerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<CandlestickSeriesApi | null>(null);
  const volumeSeriesRef = useRef<HistogramSeriesApi | null>(null);
  const [barSpacing, setBarSpacing] = useState(DEFAULT_BAR_SPACING);
  const [chartInitError, setChartInitError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [tooltipState, setTooltipState] = useState<CandleTooltipState | null>(null);

  const palette = useMemo(() => getChartPalette(), [themeMode, isExpanded]);
  const preparedData = useMemo(() => prepareMarketData(data, palette), [data, palette]);
  const tradeMarkers = useMemo(() => buildTradeMarkers(trades, palette), [trades, palette]);
  const tradeEventsByTime = useMemo(() => buildTradeEventsByTime(trades), [trades]);

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
    let cleanupCrosshair: (() => void) | null = null;
    let animationFrameA: number | null = null;
    let animationFrameB: number | null = null;

    try {
      const initialRect = container.getBoundingClientRect();
      const chart = createChart(container, {
        width: Math.max(initialRect.width || container.clientWidth, 320),
        height: Math.max(initialRect.height || container.clientHeight, 320),
        layout: {
          background: { type: ColorType.Solid, color: "rgba(0,0,0,0)" },
          textColor: palette.textColor,
        },
        grid: {
          vertLines: { color: palette.gridColor },
          horzLines: { color: palette.gridColor },
        },
        crosshair: {
          vertLine: { color: palette.crosshairColor },
          horzLine: { color: palette.crosshairColor },
        },
        rightPriceScale: {
          borderColor: palette.borderColor,
        },
        timeScale: {
          borderColor: palette.borderColor,
          barSpacing: DEFAULT_BAR_SPACING,
          rightOffset: 2,
          timeVisible: true,
        },
        handleScroll: true,
        handleScale: true,
      });

      const candlestickSeries = chart.addCandlestickSeries({
        upColor: palette.upColor,
        downColor: palette.downColor,
        borderVisible: false,
        wickUpColor: palette.upColor,
        wickDownColor: palette.downColor,
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
      candlestickSeries.setMarkers(tradeMarkers);
      chart.timeScale().applyOptions({ barSpacing });
      if (preparedData.candles.length > 0) {
        chart.timeScale().fitContent();
      }

      setChartInitError(null);

      const handleCrosshairMove = (param: MouseEventParams<Time>) => {
        if (!param.point || param.time === undefined) {
          setTooltipState(null);
          return;
        }

        const candle = param.seriesData.get(candlestickSeries) as BarData<Time> | undefined;
        if (!candle || !("open" in candle)) {
          setTooltipState(null);
          return;
        }

        const numericTime = Number(param.time);
        const containerWidth = container.clientWidth;
        const containerHeight = container.clientHeight;
        const tooltipWidth = 190;
        const tooltipHeight = 192;
        const preferredLeft = param.point.x + 14;
        const preferredTop = param.point.y + 14;

        setTooltipState({
          left: Math.min(Math.max(preferredLeft, 8), Math.max(containerWidth - tooltipWidth - 8, 8)),
          top: Math.min(Math.max(preferredTop, 8), Math.max(containerHeight - tooltipHeight - 8, 8)),
          candle: {
            time: candle.time,
            open: candle.open,
            high: candle.high,
            low: candle.low,
            close: candle.close,
          },
          volume: preparedData.volumeByTime.get(numericTime) ?? null,
          tradeEvents: tradeEventsByTime.get(numericTime) ?? [],
        });
      };

      chart.subscribeCrosshairMove(handleCrosshairMove);
      cleanupCrosshair = () => chart.unsubscribeCrosshairMove(handleCrosshairMove);

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
        window.addEventListener("resize", handleWindowResize);
        cleanupResize = () => window.removeEventListener("resize", handleWindowResize);
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
      cleanupCrosshair?.();
      setTooltipState(null);
      chartRef.current?.remove();
      chartRef.current = null;
      candlestickSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, [isExpanded, palette, preparedData.volumeByTime, tradeEventsByTime]);

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
      candlestickSeries.setMarkers(tradeMarkers);

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
      <ActionIconButton
        type="button"
        aria-label="Zoom out"
        title="Zoom out"
        onClick={() => setBarSpacing((currentSpacing) => Math.max(MIN_BAR_SPACING, Math.floor(currentSpacing / 1.2)))}
        disabled={preparedData.candles.length === 0}
      >
        <Minus className="h-4 w-4" />
      </ActionIconButton>
      <ActionIconButton
        type="button"
        aria-label="Zoom in"
        title="Zoom in"
        onClick={() => setBarSpacing((currentSpacing) => Math.min(MAX_BAR_SPACING, Math.ceil(currentSpacing * 1.2)))}
        disabled={preparedData.candles.length === 0}
      >
        <Plus className="h-4 w-4" />
      </ActionIconButton>
      <ActionIconButton
        type="button"
        aria-label="Reset zoom"
        title="Reset zoom"
        onClick={() => {
          setBarSpacing(DEFAULT_BAR_SPACING);
          chartRef.current?.timeScale().fitContent();
        }}
        disabled={preparedData.candles.length === 0}
      >
        <RotateCcw className="h-4 w-4" />
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

  return (
    <ExpandableSection
      isExpanded={isExpanded}
      onCollapse={() => setIsExpanded(false)}
      title="Executed Trades in Market"
      controls={chartControls}
      expandedClassName="chart-expanded-surface"
    >
      {chartInitError ? <p className="mb-3 text-sm text-red-300">{chartInitError}</p> : null}
      {preparedData.candles.length === 0 ? (
        <p className="mb-3 text-sm text-muted-foreground">
          Run a backtest to display market OHLCV candles and trade markers.
        </p>
      ) : null}
      <div
        className={cn("relative w-full", isExpanded ? "min-h-[420px] flex-1" : "h-[440px]")}
      >
        <div
          ref={isExpanded ? expandedContainerRef : inlineContainerRef}
          className="h-full w-full"
        />
        {tooltipState ? (
          <div
            className="pointer-events-none absolute z-10 w-[190px] rounded-md border border-border/80 bg-background/90 px-3 py-2 text-xs text-foreground shadow-xl backdrop-blur-md"
            style={{ left: tooltipState.left, top: tooltipState.top }}
          >
            <p className="mb-1 truncate text-[0.68rem] font-medium uppercase tracking-[0.14em] text-muted-foreground">
              {typeof tooltipState.candle.time === "number"
                ? formatDateTime(new Date(tooltipState.candle.time * 1000).toISOString())
                : String(tooltipState.candle.time)}
            </p>
            <div className="grid grid-cols-2 gap-x-3 gap-y-1">
              <span className="text-muted-foreground">Open</span>
              <span className="text-right tabular-nums">{formatCurrency(tooltipState.candle.open)}</span>
              <span className="text-muted-foreground">Close</span>
              <span className="text-right tabular-nums">{formatCurrency(tooltipState.candle.close)}</span>
              <span className="text-muted-foreground">Low</span>
              <span className="text-right tabular-nums">{formatCurrency(tooltipState.candle.low)}</span>
              <span className="text-muted-foreground">High</span>
              <span className="text-right tabular-nums">{formatCurrency(tooltipState.candle.high)}</span>
              <span className="text-muted-foreground">Volume</span>
              <span className="text-right tabular-nums">
                {tooltipState.volume === null ? "N/A" : formatNumber(tooltipState.volume)}
              </span>
            </div>
            {tooltipState.tradeEvents.length > 0 ? (
              <div className="mt-2 border-t border-border/70 pt-2">
                {tooltipState.tradeEvents.map((event) => (
                  <div key={`${event.trade.id}-${event.type}`} className="flex items-center justify-between gap-2">
                    <span className={event.type === "entry" ? "text-emerald-400" : "text-amber-400"}>
                      {event.type === "entry" ? "Entry" : "Exit"}
                    </span>
                    <span className="text-right tabular-nums">
                      {formatCurrency(event.type === "entry" ? event.trade.entry_price : event.trade.exit_price)}
                    </span>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </ExpandableSection>
  );
}
