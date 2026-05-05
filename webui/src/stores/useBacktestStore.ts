import { create } from "zustand";

import { checkStrategyCode, fetchCsvFiles, runBacktest, uploadCsvFile } from "@/features/backtest/api";
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
  csvFiles: string[];
  csvFilesError: string | null;
  isCsvFilesLoading: boolean;
  isCsvUploading: boolean;
  runStatus: BacktestRunStatus | null;
  validationResult: StrategyValidationResult | null;
  setSettings: (settings: BacktestSettings) => void;
  loadCsvFiles: () => Promise<void>;
  uploadCsv: (file: File) => Promise<void>;
  runValidation: (strategyFilename?: string) => Promise<StrategyValidationResult | null>;
  runCurrentBacktest: (strategyFilename?: string) => Promise<void>;
}

export const useBacktestStore = create<BacktestState>((set, get) => ({
  isRunning: false,
  isValidating: false,
  settings: defaultBacktestSettings,
  backtestResult: null,
  csvFiles: [],
  csvFilesError: null,
  isCsvFilesLoading: false,
  isCsvUploading: false,
  runStatus: null,
  validationResult: null,
  setSettings: (settings) =>
    set({
      settings,
    }),
  loadCsvFiles: async () => {
    set({ isCsvFilesLoading: true, csvFilesError: null });

    try {
      const csvFiles = await fetchCsvFiles();
      set((state) => ({
        csvFiles,
        settings:
          state.settings.dataSource === "csv" && !state.settings.csvFilename && csvFiles.length > 0
            ? {
                ...state.settings,
                csvFilename: csvFiles[0],
              }
            : state.settings,
      }));
    } catch (error) {
      set({
        csvFilesError: error instanceof Error ? error.message : "Unable to fetch CSV files.",
      });
    } finally {
      set({ isCsvFilesLoading: false });
    }
  },
  uploadCsv: async (file) => {
    set({ isCsvUploading: true, csvFilesError: null });

    try {
      const response = await uploadCsvFile(file);
      set((state) => ({
        csvFiles: response.files,
        settings: {
          ...state.settings,
          dataSource: "csv",
          csvFilename: response.filename,
        },
      }));
    } catch (error) {
      set({
        csvFilesError: error instanceof Error ? error.message : "Unable to upload CSV file.",
      });
    } finally {
      set({ isCsvUploading: false });
    }
  },
  runValidation: async (strategyFilename) => {
    set({ isValidating: true, runStatus: null });

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
        validationResult: null,
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
      const response = await runBacktest({
        data:
          settings.dataSource === "csv"
            ? {
                source: "csv",
                filename: settings.csvFilename,
              }
            : {
                source: "yahoo",
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

      if (response.strategy_validation) {
        set({
          validationResult: response.strategy_validation,
          backtestResult: null,
          runStatus: null,
        });
        return;
      }

      if (!response.backtest_result) {
        throw new Error("Backtest response missing result payload.");
      }

      set({
        validationResult: null,
        backtestResult: response.backtest_result,
        runStatus: {
          tone: "success",
          message: "Backtest completed successfully.",
        },
      });
    } catch (error) {
      set({
        validationResult: null,
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
