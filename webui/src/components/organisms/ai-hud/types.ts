export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  markdown: string;
  strategyCode?: string;
  isStrategyGeneration?: boolean;
}

export interface ProgressStep {
  stepId: string;
  label: string;
  state: "running" | "done";
}
