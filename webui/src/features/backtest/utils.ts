import { cn } from "@/lib/utils";
import type { KpiMetricTone, TradeSide } from "@/types/backtest";

interface ToneStyles {
  iconClassName: string;
  valueClassName: string;
  strokeColor: string;
}

const TONE_STYLES: Record<KpiMetricTone, ToneStyles> = {
  positive: {
    iconClassName: "text-emerald-500",
    valueClassName: "text-emerald-500",
    strokeColor: "rgb(16 185 129)",
  },
  neutral: {
    iconClassName: "text-blue-500",
    valueClassName: "",
    strokeColor: "rgb(59 130 246)",
  },
  negative: {
    iconClassName: "text-rose-500",
    valueClassName: "text-rose-500",
    strokeColor: "rgb(244 63 94)",
  },
};

const TRADE_SIDE_BADGE_STYLES: Record<TradeSide, string> = {
  LONG: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-[0_0_10px_rgba(16,185,129,0.2)]",
  SHORT: "bg-rose-500/10 text-rose-400 border border-rose-500/20 shadow-[0_0_10px_rgba(244,63,94,0.2)]",
};

export function formatCurrency(value: number): string {
  return value.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  });
}

export function formatNumber(value: number): string {
  return value.toLocaleString("en-US", {
    maximumFractionDigits: 4,
  });
}

export function formatPercent(value: number): string {
  return `${value.toFixed(2)}%`;
}

export function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

export function getKpiToneStyles(tone: KpiMetricTone): ToneStyles {
  return TONE_STYLES[tone];
}

export function getTradeRowClassName(index: number): string {
  return cn("border-border/80", index % 2 === 0 ? "bg-muted/30" : "bg-transparent");
}

export function getTradeSideBadgeClassName(side: TradeSide): string {
  return cn("px-2 py-1 rounded-md text-xs font-semibold", TRADE_SIDE_BADGE_STYLES[side]);
}

export function getTradePnlClassName(pnl: number): string {
  let pnlClassName = "text-muted-foreground";

  if (pnl > 0) {
    pnlClassName = "text-emerald-500";
  } else if (pnl < 0) {
    pnlClassName = "text-rose-500";
  }

  return cn("text-right font-medium", pnlClassName);
}

export function formatKpiLabel(key: string): string {
  return key
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function formatKpiValue(key: string, value: number | string | null): string {
  if (value === null) {
    return "N/A";
  }

  if (typeof value === "string") {
    return value;
  }

  if (key.includes("_pct")) {
    return formatPercent(value);
  }

  if (key === "total_trades" || key.includes("bars_count")) {
    return formatNumber(value);
  }

  if (
    key.includes("pnl") ||
    key.includes("balance") ||
    key.includes("fees") ||
    key.includes("profit") ||
    key.includes("loss") ||
    key === "expectancy" ||
    key === "avg_win" ||
    key === "avg_loss" ||
    key === "best_trade" ||
    key === "worst_trade" ||
    key === "median_trade"
  ) {
    return formatCurrency(value);
  }

  return formatNumber(value);
}
