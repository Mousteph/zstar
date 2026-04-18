export interface AssistantGenerateRequest {
  message: string;
  model?: string;
}

export interface AssistantGenerateResponse {
  markdown: string;
}
