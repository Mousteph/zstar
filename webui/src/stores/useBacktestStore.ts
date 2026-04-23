import { create } from "zustand";

import { runBacktest } from "@/features/backtest/api";
import { defaultBacktestSettings } from "@/features/backtest/defaults";
import type { BacktestRunResponse, BacktestRunStatus, BacktestSettings } from "@/types/backtest";

interface BacktestState {
  isRunning: boolean;
  settings: BacktestSettings;
  backtestResult: BacktestRunResponse | null;
  runStatus: BacktestRunStatus | null;
  setSettings: (settings: BacktestSettings) => void;
  runCurrentBacktest: (strategyFilename?: string) => Promise<void>;
}

export const useBacktestStore = create<BacktestState>((set, get) => ({
  isRunning: false,
  settings: defaultBacktestSettings,
  backtestResult: null,
  runStatus: null,
  setSettings: (settings) =>
    set({
      settings,
    }),
  runCurrentBacktest: async (strategyFilename) => {
    const { settings } = get();
    set({ isRunning: true, runStatus: null });

    const slippageSeed = settings.slippageSeed.trim();
    const parsedSlippageSeed = slippageSeed ? Number(slippageSeed) : undefined;
    const slippageSeedPayload =
      parsedSlippageSeed !== undefined && Number.isFinite(parsedSlippageSeed)
        ? parsedSlippageSeed
        : undefined;

    try {
      const result = await runBacktest({
        data: {
          symbol: settings.symbol,
          start_date: settings.startDate,
          end_date: settings.endDate,
          interval: settings.interval,
        },
        ...(strategyFilename ? { strategy_filename: strategyFilename } : {}),
        backtest_config: {
          initial_balance: settings.initialBalance,
          entry_fee_pct: settings.entryFeePct,
          exit_fee_pct: settings.exitFeePct,
          slippage_pct: settings.slippagePct,
          ...(slippageSeedPayload === undefined ? {} : { slippage_seed: slippageSeedPayload }),
        },
      });

      set({
        backtestResult: result,
        runStatus: {
          tone: "success",
          message: "Backtest completed successfully.",
        },
      });
    } catch (error) {
      set({
        runStatus: {
          tone: "error",
          message: error instanceof Error ? error.message : "Backtest failed.",
        },
      });
    } finally {
      set({ isRunning: false });
    }
  },
}));
