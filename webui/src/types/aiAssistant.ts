export interface AssistantGenerateRequest {
  message: string;
  model?: string;
}

export interface AssistantStatusEvent {
  type: "status";
  step_id: string;
  label: string;
  state: "running" | "done";
}

export interface AssistantFinalEvent {
  type: "final";
  markdown: string;
  strategy_code: string;
  is_strategy_generation: boolean;
}

export interface AssistantErrorEvent {
  type: "error";
  detail: string;
}

export type AssistantStreamEvent = AssistantStatusEvent | AssistantFinalEvent | AssistantErrorEvent;
