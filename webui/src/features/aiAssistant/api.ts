import type { AssistantEchoRequest, AssistantEchoResponse } from "@/types/aiAssistant";

export async function sendAssistantEcho(
  payload: AssistantEchoRequest,
): Promise<AssistantEchoResponse> {
  const response = await fetch("/api/ai-assistant/echo", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const responseJson = (await response.json()) as
    | AssistantEchoResponse
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

  return responseJson as AssistantEchoResponse;
}
