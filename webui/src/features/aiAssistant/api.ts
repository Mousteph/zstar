import type { AssistantGenerateRequest, AssistantGenerateResponse } from "@/types/aiAssistant";

export async function sendAssistantGenerate(
  payload: AssistantGenerateRequest,
): Promise<AssistantGenerateResponse> {
  const response = await fetch("/api/ai-assistant/generate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const responseJson = (await response.json()) as
    | AssistantGenerateResponse
    | {
        detail?: string;
      };

  if (!response.ok) {
    const detail =
      "detail" in responseJson && typeof responseJson.detail === "string"
        ? responseJson.detail
        : "Assistant request failed. Please try again.";
    throw new Error(detail);
  }

  return responseJson as AssistantGenerateResponse;
}
