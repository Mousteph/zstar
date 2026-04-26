import type {
  BacktestRunRequest,
  BacktestRunResponse,
  StrategiesResponse,
  StrategyValidationResult,
  ValidateStrategyRequest,
} from "@/types/backtest";

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

export async function fetchStrategies(): Promise<string[]> {
  const response = await fetch("/api/strategies", {
    method: "GET",
  });

  const responseJson = (await response.json()) as
    | StrategiesResponse
    | {
        detail?: string;
      };

  if (!response.ok) {
    const detail =
      "detail" in responseJson && typeof responseJson.detail === "string"
        ? responseJson.detail
        : "Unable to fetch strategies.";
    throw new Error(detail);
  }

  if (!("strategies" in responseJson) || !Array.isArray(responseJson.strategies)) {
    throw new Error("Invalid strategies response payload.");
  }

  return responseJson.strategies;
}

export async function checkStrategyCode(payload: ValidateStrategyRequest): Promise<StrategyValidationResult> {
  const response = await fetch("/api/validate-strategies", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const responseJson = (await response.json()) as
    | StrategyValidationResult
    | {
        detail?: string;
      };

  if (!response.ok) {
    const detail =
      "detail" in responseJson && typeof responseJson.detail === "string"
        ? responseJson.detail
        : "Unable to validate strategy.";
    throw new Error(detail);
  }

  if (
    !("issues" in responseJson) ||
    !Array.isArray(responseJson.issues) ||
    !("ready_to_backtest" in responseJson) ||
    typeof responseJson.ready_to_backtest !== "boolean"
  ) {
    throw new Error("Invalid strategy validation response payload.");
  }

  return responseJson as StrategyValidationResult;
}
