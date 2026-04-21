export type KpiMetricTone = "positive" | "neutral" | "negative";
export type KpiMetricIcon = "trending-up" | "activity" | "trending-down";

export type TradeSide = "LONG" | "SHORT";

export interface BacktestSettings {
  symbol: string;
  startDate: string;
  endDate: string;
  interval: string;
  initialBalance: number;
  entryFeePct: number;
  exitFeePct: number;
  slippagePct: number;
  slippageSeed: string;
}

export interface BacktestRunStatus {
  tone: "success" | "error";
  message: string;
}

export interface BacktestRunRequest {
  data: {
    symbol: string;
    start_date: string;
    end_date: string;
    interval: string;
  };
  backtest_config: {
    initial_balance: number;
    entry_fee_pct: number;
    exit_fee_pct: number;
    slippage_pct: number;
    slippage_seed?: number;
  };
}

export interface EquityPoint {
  datetime: string;
  strategy: number | null;
  buy_and_hold: number | null;
}

export interface MarketOhlcvPoint {
  datetime: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
}

export interface Trade {
  id: string;
  symbol: string;
  side: TradeSide;
  size: number;
  entry_price: number;
  exit_price: number;
  entry_datetime: string;
  exit_datetime: string;
  raw_pnl: number;
  total_fees: number;
  net_pnl: number;
}

export interface BacktestMeta {
  symbol: string;
  start_date: string;
  end_date: string;
  interval: string;
  bars_count: number;
}

export interface KpiMetric {
  id: string;
  label: string;
  value: string;
  description: string;
  tone: KpiMetricTone;
  icon: KpiMetricIcon;
}

export interface KpiRow {
  key: string;
  label: string;
  value: string;
}

export interface BacktestRunResponse {
  equity_curve: EquityPoint[];
  market_ohlcv: MarketOhlcvPoint[];
  trades: Trade[];
  kpis: Record<string, number | string | null>;
  meta: BacktestMeta;
}
