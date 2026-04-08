import type { BacktestRunRequest, BacktestRunResponse } from "@/types/backtest";

export async function runBacktest(payload: BacktestRunRequest): Promise<BacktestRunResponse> {
  const response = await fetch("/api/backtest/run", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const responseJson = (await response.json()) as
    | BacktestRunResponse
    | {
        detail?: string;
      };

  if (!response.ok) {
    const detail =
      "detail" in responseJson && typeof responseJson.detail === "string"
        ? responseJson.detail
        : "Backtest failed. Please check your strategy and settings.";
    throw new Error(detail);
  }

  return responseJson as BacktestRunResponse;
}
