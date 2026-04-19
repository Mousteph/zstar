import type {
  AssistantFinalEvent,
  AssistantGenerateRequest,
  AssistantStatusEvent,
  AssistantStreamEvent,
} from "@/types/aiAssistant";

interface AssistantGenerateStreamOptions {
  onStatus?: (event: AssistantStatusEvent) => void;
}

function parseLineEvent(line: string): AssistantStreamEvent {
  return JSON.parse(line) as AssistantStreamEvent;
}

function parseStreamChunk(
  chunk: string,
  onEvent: (event: AssistantStreamEvent) => void,
): void {
  const line = chunk.trim();
  if (!line) {
    return;
  }
  onEvent(parseLineEvent(line));
}

export async function sendAssistantGenerateStream(
  payload: AssistantGenerateRequest,
  options: AssistantGenerateStreamOptions = {},
): Promise<AssistantFinalEvent> {
  const response = await fetch("/api/ai-assistant/generate-stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let detail = "Assistant request failed. Please try again.";
    try {
      const responseJson = (await response.json()) as { detail?: string };
      if (typeof responseJson.detail === "string" && responseJson.detail.trim()) {
        detail = responseJson.detail;
      }
    } catch {
      // Use default error when body is not JSON.
    }
    throw new Error(detail);
  }

  if (!response.body) {
    throw new Error("Assistant stream is unavailable. Please try again.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalEvent: AssistantFinalEvent | null = null;

  const handleEvent = (event: AssistantStreamEvent) => {
    if (event.type === "status") {
      options.onStatus?.(event);
      return;
    }

    if (event.type === "final") {
      finalEvent = event;
      return;
    }

    if (event.type === "error") {
      throw new Error(event.detail || "Assistant generation failed.");
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });

    let newlineIndex = buffer.indexOf("\n");
    while (newlineIndex !== -1) {
      const line = buffer.slice(0, newlineIndex);
      buffer = buffer.slice(newlineIndex + 1);
      parseStreamChunk(line, handleEvent);
      if (finalEvent !== null) {
        await reader.cancel();
        return finalEvent;
      }
      newlineIndex = buffer.indexOf("\n");
    }

    if (done) {
      break;
    }
  }

  if (buffer.trim()) {
    parseStreamChunk(buffer, handleEvent);
    if (finalEvent !== null) {
      return finalEvent;
    }
  }

  if (finalEvent === null) {
    throw new Error("Assistant stream ended before returning a final response.");
  }

  return finalEvent;
}
