import type { BacktestSettings } from "@/types/backtest";

export const defaultBacktestSettings: BacktestSettings = {
  symbol: "AAPL",
  startDate: "2024-01-01",
  endDate: "2025-01-01",
  interval: "1d",
  initialBalance: 100000,
  entryFeePct: 0.05,
  exitFeePct: 0.05,
  slippagePct: 0.02,
  slippageSeed: "42",
};
