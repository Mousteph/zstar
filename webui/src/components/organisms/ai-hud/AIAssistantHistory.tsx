"use client";

import { Check, ClipboardCheck, Copy, FileCode2, LoaderCircle, Trash2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { RefObject } from "react";

import { hasCodeBlock, markdownComponents } from "@/components/organisms/ai-hud/markdownComponents";
import type { ChatMessage, ProgressStep } from "@/components/organisms/ai-hud/types";

interface AIAssistantHistoryProps {
  readonly messages: ChatMessage[];
  readonly progressSteps: ProgressStep[];
  readonly isSending: boolean;
  readonly hasMessages: boolean;
  readonly copiedMessageId: string | null;
  readonly historyRef: RefObject<HTMLDivElement | null>;
  readonly onClearConversation: () => void;
  readonly onCopyStrategyCode: (messageId: string, strategyCode: string) => Promise<void>;
  readonly onApplyStrategyCode: (strategyCode: string) => void;
}

export function AIAssistantHistory({
  messages,
  progressSteps,
  isSending,
  hasMessages,
  copiedMessageId,
  historyRef,
  onClearConversation,
  onCopyStrategyCode,
  onApplyStrategyCode,
}: Readonly<AIAssistantHistoryProps>) {
  return (
    <div className="zstar-ai-hud__floating-lane">
      {hasMessages ? (
        <div className="zstar-ai-hud__clear-floating">
          <button
            type="button"
            className="zstar-ai-hud__clear-button"
            onClick={onClearConversation}
            disabled={isSending || !hasMessages}
            aria-label="Clear conversation"
            title="Clear conversation"
          >
            <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Clear</span>
          </button>
        </div>
      ) : null}

      <div className="zstar-ai-hud__history-shell">
        <div
          ref={historyRef}
          className={`zstar-ai-hud__history ${hasMessages ? "zstar-ai-hud__history--with-clear" : ""}`}
          role="status"
          aria-live="polite"
          onWheel={(event) => {
            event.stopPropagation();
          }}
          onTouchMove={(event) => {
            event.stopPropagation();
          }}
        >
          {messages.map((message) => (
            <article
              key={message.id}
              className={`zstar-ai-hud__message zstar-ai-hud__message--${message.role} zstar-ai-hud__message--pop`}
            >
              {message.role === "assistant" ? (
                <div
                  className={`zstar-ai-hud__assistant-content zstar-ai-hud__markdown ${hasCodeBlock(message.markdown) ? "zstar-ai-hud__assistant-content--code" : ""}`}
                >
                  <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                    {message.markdown}
                  </ReactMarkdown>
                  {message.isStrategyGeneration && message.strategyCode ? (
                    <div className="zstar-ai-hud__strategy-actions">
                      <button
                        type="button"
                        className="zstar-ai-hud__strategy-action-button"
                        onClick={() => {
                          void onCopyStrategyCode(message.id, message.strategyCode ?? "");
                        }}
                        title="Copy strategy code"
                        aria-label="Copy strategy code"
                      >
                        {copiedMessageId === message.id ? (
                          <ClipboardCheck className="h-3.5 w-3.5" aria-hidden="true" />
                        ) : (
                          <Copy className="h-3.5 w-3.5" aria-hidden="true" />
                        )}
                      </button>

                      <button
                        type="button"
                        className="zstar-ai-hud__strategy-action-button"
                        onClick={() => {
                          if (!message.strategyCode) {
                            return;
                          }
                          onApplyStrategyCode(message.strategyCode);
                        }}
                        title="Insert strategy code into editor"
                        aria-label="Insert strategy code into editor"
                      >
                        <FileCode2 className="h-3.5 w-3.5" aria-hidden="true" />
                      </button>
                    </div>
                  ) : null}
                </div>
              ) : (
                <p className="zstar-ai-hud__user-bubble">{message.markdown}</p>
              )}
            </article>
          ))}

          {isSending && progressSteps.length > 0 ? (
            <div className="zstar-ai-hud__progress" aria-live="polite">
              {progressSteps.map((step) => (
                <p key={step.stepId} className="zstar-ai-hud__progress-row">
                  {step.state === "done" ? (
                    <Check className="zstar-ai-hud__progress-done h-3.5 w-3.5" aria-hidden="true" />
                  ) : (
                    <LoaderCircle className="zstar-ai-hud__progress-running h-3.5 w-3.5" aria-hidden="true" />
                  )}
                  <span>{step.label}</span>
                </p>
              ))}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
