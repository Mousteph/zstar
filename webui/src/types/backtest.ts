export type KpiMetricTone = "positive" | "neutral" | "negative";
export type KpiMetricIcon = "trending-up" | "activity" | "trending-down";

export type TradeSide = "LONG" | "SHORT";
export type BacktestDataSource = "yahoo" | "csv";

export interface BacktestSettings {
  dataSource: BacktestDataSource;
  symbol: string;
  startDate: string;
  endDate: string;
  interval: string;
  csvFilename: string;
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

export type ValidationCategory = "syntax" | "template" | "type" | "logic";

export interface ValidationIssue {
  category: ValidationCategory;
  file: string;
  line: number | null;
  message: string;
}

export interface StrategyValidationResult {
  strategy_filename: string;
  ready_to_backtest: boolean;
  total_errors: number;
  issues: ValidationIssue[];
  summary_text: string;
}

export interface ValidateStrategyRequest {
  strategy_filename?: string;
}

export interface BacktestRunRequest {
  data:
    | {
        source: "yahoo";
        symbol: string;
        start_date: string;
        end_date: string;
        interval: string;
      }
    | {
        source: "csv";
        filename: string;
      };
  strategy_filename?: string;
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
  take_profit_price: number | null;
  stop_loss_price: number | null;
  exit_reason: string;
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

export interface BacktestRunEnvelopeResponse {
  strategy_validation: StrategyValidationResult | null;
  backtest_result: BacktestRunResponse | null;
}

export interface StrategiesResponse {
  strategies: string[];
}

export interface CsvFilesResponse {
  files: string[];
}

export interface CsvFileUploadResponse {
  filename: string;
  files: string[];
}
