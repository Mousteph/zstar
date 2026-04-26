import { create } from "zustand";

import { checkStrategyCode, runBacktest } from "@/features/backtest/api";
import { defaultBacktestSettings } from "@/features/backtest/defaults";
import type {
  BacktestRunResponse,
  BacktestRunStatus,
  BacktestSettings,
  StrategyValidationResult,
} from "@/types/backtest";

interface BacktestState {
  isRunning: boolean;
  isValidating: boolean;
  settings: BacktestSettings;
  backtestResult: BacktestRunResponse | null;
  runStatus: BacktestRunStatus | null;
  validationResult: StrategyValidationResult | null;
  setSettings: (settings: BacktestSettings) => void;
  runValidation: (strategyFilename?: string) => Promise<StrategyValidationResult | null>;
  exportValidationReport: (format: "txt" | "json") => void;
  runCurrentBacktest: (strategyFilename?: string) => Promise<void>;
}

function downloadValidationReport(content: string, filename: string, mimeType: string): void {
  if (typeof window === "undefined") {
    return;
  }

  const blob = new Blob([content], { type: mimeType });
  const url = window.URL.createObjectURL(blob);
  const anchor = window.document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.URL.revokeObjectURL(url);
}

function validationReportAsText(result: StrategyValidationResult): string {
  const lines: string[] = [
    `strategy_filename: ${result.strategy_filename}`,
    `ready_to_backtest: ${result.ready_to_backtest}`,
    `total_errors: ${result.total_errors}`,
    `summary_text: ${result.summary_text}`,
    "issues:",
  ];

  for (const issue of result.issues) {
    const location = issue.line === null ? issue.file : `${issue.file}:${issue.line}`;
    lines.push(`- [${issue.severity}] [${issue.category}] ${location} - ${issue.message}`);
  }

  return lines.join("\n");
}

export const useBacktestStore = create<BacktestState>((set, get) => ({
  isRunning: false,
  isValidating: false,
  settings: defaultBacktestSettings,
  backtestResult: null,
  runStatus: null,
  validationResult: null,
  setSettings: (settings) =>
    set({
      settings,
    }),
  runValidation: async (strategyFilename) => {
    set({ isValidating: true });

    try {
      const validationResult = await checkStrategyCode(
        strategyFilename ? { strategy_filename: strategyFilename } : {}
      );

      set({
        validationResult,
      });

      return validationResult;
    } catch (error) {
      set({
        runStatus: {
          tone: "error",
          message: error instanceof Error ? error.message : "Strategy validation failed.",
        },
      });
      return null;
    } finally {
      set({ isValidating: false });
    }
  },
  exportValidationReport: (format) => {
    const validationResult = get().validationResult;
    if (!validationResult) {
      return;
    }

    if (format === "json") {
      downloadValidationReport(
        JSON.stringify(validationResult, null, 2),
        `${validationResult.strategy_filename}.validation.json`,
        "application/json"
      );
      return;
    }

    downloadValidationReport(
      validationReportAsText(validationResult),
      `${validationResult.strategy_filename}.validation.txt`,
      "text/plain"
    );
  },
  runCurrentBacktest: async (strategyFilename) => {
    const { settings, runValidation } = get();
    set({ isRunning: true, runStatus: null });

    const validationResult = await runValidation(strategyFilename);
    if (!validationResult) {
      set({ isRunning: false });
      return;
    }

    if (!validationResult.ready_to_backtest) {
      set({
        runStatus: {
          tone: "error",
          message: "Backtest blocked: fix validation errors first.",
        },
        isRunning: false,
      });
      return;
    }

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
