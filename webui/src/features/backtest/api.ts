import type {
  BacktestRunEnvelopeResponse,
  BacktestRunRequest,
  CsvFilesResponse,
  CsvFileUploadResponse,
  StrategiesResponse,
  StrategyValidationResult,
  ValidateStrategyRequest,
} from "@/types/backtest";

export async function runBacktest(payload: BacktestRunRequest): Promise<BacktestRunEnvelopeResponse> {
  const response = await fetch("/api/backtest/run", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const responseJson = (await response.json()) as
    | BacktestRunEnvelopeResponse
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

  if (
    !("strategy_validation" in responseJson) ||
    !("backtest_result" in responseJson)
  ) {
    throw new Error("Invalid run backtest response payload.");
  }

  return responseJson;
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

  const responseJson = (await response.json()) as StrategyValidationResult;

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

  return responseJson;
}

export async function fetchCsvFiles(): Promise<string[]> {
  const response = await fetch("/api/backtest/csv-files", {
    method: "GET",
  });

  const responseJson = (await response.json()) as
    | CsvFilesResponse
    | {
        detail?: string;
      };

  if (!response.ok) {
    const detail =
      "detail" in responseJson && typeof responseJson.detail === "string"
        ? responseJson.detail
        : "Unable to fetch CSV files.";
    throw new Error(detail);
  }

  if (!("files" in responseJson) || !Array.isArray(responseJson.files)) {
    throw new Error("Invalid CSV files response payload.");
  }

  return responseJson.files;
}

export async function uploadCsvFile(file: File): Promise<CsvFileUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/api/backtest/csv-files", {
    method: "POST",
    body: formData,
  });

  const responseJson = (await response.json()) as
    | CsvFileUploadResponse
    | {
        detail?: string;
      };

  if (!response.ok) {
    const detail =
      "detail" in responseJson && typeof responseJson.detail === "string"
        ? responseJson.detail
        : "Unable to upload CSV file.";
    throw new Error(detail);
  }

  if (
    !("filename" in responseJson) ||
    typeof responseJson.filename !== "string" ||
    !("files" in responseJson) ||
    !Array.isArray(responseJson.files)
  ) {
    throw new Error("Invalid CSV upload response payload.");
  }

  return responseJson;
}
