import type {
  BacktestRunEnvelopeResponse,
  BacktestRunRequest,
  CsvFilesResponse,
  CsvFileUploadResponse,
  StrategiesResponse,
  StrategyValidationResult,
  ValidateStrategyRequest,
} from "@/types/backtest";

type ErrorPayload = {
  detail?: string;
};

async function readResponsePayload<T>(response: Response, fallbackMessage: string): Promise<T | ErrorPayload> {
  const text = await response.text();
  if (!text) {
    return response.ok ? ({} as T) : { detail: fallbackMessage };
  }

  try {
    return JSON.parse(text) as T | ErrorPayload;
  } catch {
    return { detail: response.ok ? "Invalid JSON response payload." : text || fallbackMessage };
  }
}

function errorDetail(payload: unknown, fallbackMessage: string): string {
  return payload &&
    typeof payload === "object" &&
    "detail" in payload &&
    typeof payload.detail === "string" ? payload.detail : fallbackMessage;
}

export async function runBacktest(payload: BacktestRunRequest): Promise<BacktestRunEnvelopeResponse> {
  const response = await fetch("/api/backtest/run", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const responseJson = await readResponsePayload<BacktestRunEnvelopeResponse>(
    response,
    "Backtest failed. Please check your strategy and settings.",
  );

  if (!response.ok) {
    throw new Error(errorDetail(responseJson, "Backtest failed. Please check your strategy and settings."));
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

  const responseJson = await readResponsePayload<StrategiesResponse>(response, "Unable to fetch strategies.");

  if (!response.ok) {
    throw new Error(errorDetail(responseJson, "Unable to fetch strategies."));
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

  const responseJson = await readResponsePayload<StrategyValidationResult>(response, "Unable to validate strategy.");

  if (!response.ok) {
    throw new Error(errorDetail(responseJson, "Unable to validate strategy."));
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

  const responseJson = await readResponsePayload<CsvFilesResponse>(response, "Unable to fetch CSV files.");

  if (!response.ok) {
    throw new Error(errorDetail(responseJson, "Unable to fetch CSV files."));
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

  const responseJson = await readResponsePayload<CsvFileUploadResponse>(response, "Unable to upload CSV file.");

  if (!response.ok) {
    throw new Error(errorDetail(responseJson, "Unable to upload CSV file."));
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
