import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import {
  ArrowUp,
  Check,
  ClipboardCheck,
  Copy,
  FileCode2,
  LoaderCircle,
  Trash2,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import remarkGfm from "remark-gfm";

import { sendAssistantGenerateStream } from "@/features/aiAssistant/api";
import type { AssistantStatusEvent } from "@/types/aiAssistant";

const HOVER_MEDIA_QUERY = "(hover: hover) and (pointer: fine)";
const MAX_HUD_HEIGHT_RATIO = 0.7;
const MAX_TEXTAREA_HEIGHT_RATIO = 0.4;
const MIN_TEXTAREA_HEIGHT = 96;

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  markdown: string;
  strategyCode?: string;
  isStrategyGeneration?: boolean;
}

interface ProgressStep {
  stepId: string;
  label: string;
  state: "running" | "done";
}

interface AIAssistantHudProps {
  readonly onApplyStrategyCode?: (code: string) => void;
}

function getInitialCanHover(): boolean {
  if (globalThis.window === undefined) {
    return false;
  }

  return globalThis.window.matchMedia(HOVER_MEDIA_QUERY).matches;
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }

  return "Assistant request failed. Please try again.";
}

function hasCodeBlock(markdown: string): boolean {
  return markdown.includes("```");
}

function getCodeContent(children: ReactNode): string {
  if (typeof children === "string" || typeof children === "number") {
    return String(children).replace(/\n$/, "");
  }

  if (Array.isArray(children)) {
    return children.map((child) => getCodeContent(child)).join("").replace(/\n$/, "");
  }

  return "";
}

const markdownComponents: Components = {
  code({ children, className, ...props }) {
    const codeContent = getCodeContent(children);
    const languageMatch = /language-([\w-]+)/.exec(className ?? "");
    const isCodeBlock = Boolean(languageMatch) || codeContent.includes("\n");

    if (isCodeBlock) {
      return (
        <div className="zstar-ai-hud__code-block">
          <SyntaxHighlighter
            language={languageMatch?.[1] ?? "text"}
            style={oneDark}
            wrapLongLines={false}
            customStyle={{
              margin: 0,
              padding: "0.9rem 1rem",
              borderRadius: "0.72rem",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              background: "rgba(6, 10, 20, 0.96)",
              fontSize: "0.82rem",
              lineHeight: 1.5,
            }}
            codeTagProps={{
              style: {
                fontFamily: "var(--font-mono)",
              },
            }}
          >
            {codeContent}
          </SyntaxHighlighter>
        </div>
      );
    }

    return (
      <code className={className} {...props}>
        {children}
      </code>
    );
  },
};


function createIsEventInsideHud(
  expandedRef: React.RefObject<HTMLDivElement | null>,
  buttonRef: React.RefObject<HTMLButtonElement | null>,
): (target: EventTarget | null) => boolean {
  return (target: EventTarget | null): boolean => {
    if (!(target instanceof Node)) {
      return false;
    }

    return Boolean(expandedRef.current?.contains(target) || buttonRef.current?.contains(target));
  };
}

export function AIAssistantHud({
  onApplyStrategyCode,
}: Readonly<AIAssistantHudProps>) {
  const expandedRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const historyRef = useRef<HTMLDivElement>(null);
  const [canHover, setCanHover] = useState(getInitialCanHover);
  const [isHovered, setIsHovered] = useState(false);
  const [isPinned, setIsPinned] = useState(false);
  const [draftMessage, setDraftMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [composerError, setComposerError] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [progressSteps, setProgressSteps] = useState<ProgressStep[]>([]);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);

  const isExpanded = isPinned;
  const hasMessages = messages.length > 0;
  const hasConversation = hasMessages || isSending;

  const resizeTextarea = () => {
    const textareaElement = textareaRef.current;
    if (!textareaElement || globalThis.window === undefined) {
      return;
    }

    const maxHudHeight = Math.floor(globalThis.window.innerHeight * MAX_HUD_HEIGHT_RATIO);
    const maxTextareaHeight = Math.max(
      MIN_TEXTAREA_HEIGHT,
      Math.floor(globalThis.window.innerHeight * MAX_TEXTAREA_HEIGHT_RATIO),
    );
    const boundedTextareaMaxHeight = Math.min(
      maxTextareaHeight,
      Math.max(MIN_TEXTAREA_HEIGHT, maxHudHeight - 180),
    );

    textareaElement.style.maxHeight = `${boundedTextareaMaxHeight}px`;
    textareaElement.style.height = "auto";

    const nextHeight = Math.min(textareaElement.scrollHeight, boundedTextareaMaxHeight);
    textareaElement.style.height = `${nextHeight}px`;
    textareaElement.style.overflowY =
      textareaElement.scrollHeight > boundedTextareaMaxHeight ? "auto" : "hidden";
  };

  useEffect(() => {
    if (globalThis.window === undefined) {
      return;
    }

    const mediaQueryList = globalThis.window.matchMedia(HOVER_MEDIA_QUERY);
    const handleMediaQueryChange = (event: MediaQueryListEvent) => {
      setCanHover(event.matches);
      if (!event.matches) {
        setIsHovered(false);
      }
    };

    setCanHover(mediaQueryList.matches);
    mediaQueryList.addEventListener("change", handleMediaQueryChange);

    return () => {
      mediaQueryList.removeEventListener("change", handleMediaQueryChange);
    };
  }, []);

  useEffect(() => {
    if (!isPinned || globalThis.window === undefined) {
      return;
    }

    globalThis.window.requestAnimationFrame(() => {
      resizeTextarea();
      textareaRef.current?.focus({ preventScroll: true });
    });
  }, [isPinned]);

  useEffect(() => {
    if (!isPinned || globalThis.window === undefined) {
      return;
    }

    const handleWindowResize = () => {
      resizeTextarea();
    };

    globalThis.window.addEventListener("resize", handleWindowResize);
    return () => {
      globalThis.window.removeEventListener("resize", handleWindowResize);
    };
  }, [isPinned]);

  useEffect(() => {
    if (!isExpanded || !historyRef.current) {
      return;
    }

    historyRef.current.scrollTop = historyRef.current.scrollHeight;
  }, [isExpanded, messages, isSending, progressSteps]);

  useEffect(() => {
    if (!isExpanded) {
      return;
    }

    const isEventInsideHud = createIsEventInsideHud(expandedRef, buttonRef);

    const collapseHud = () => {
      setIsHovered(false);
      setIsPinned(false);

      if (
        document.activeElement instanceof HTMLElement &&
        (expandedRef.current?.contains(document.activeElement) ||
          buttonRef.current?.contains(document.activeElement))
      ) {
        document.activeElement.blur();
      }
    };

    const handlePointerDown = (event: PointerEvent) => {
      if (isEventInsideHud(event.target)) {
        return;
      }

      collapseHud();
    };

    document.addEventListener("pointerdown", handlePointerDown);

    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
    };
  }, [isExpanded]);

  const handleExpandAndFocus = () => {
    setComposerError(null);
    setIsPinned(true);
  };

  const handleStatusEvent = (event: AssistantStatusEvent) => {
    setProgressSteps((currentSteps) => {
      const existingStepIndex = currentSteps.findIndex((step) => step.stepId === event.step_id);
      const nextStep: ProgressStep = {
        stepId: event.step_id,
        label: event.label,
        state: event.state,
      };

      if (existingStepIndex === -1) {
        return [...currentSteps, nextStep];
      }

      return currentSteps.map((step, index) => (index === existingStepIndex ? nextStep : step));
    });
  };

  const handleCopyStrategyCode = async (messageId: string, strategyCode: string) => {
    if (!strategyCode.trim() || globalThis.navigator?.clipboard === undefined) {
      return;
    }

    try {
      await globalThis.navigator.clipboard.writeText(strategyCode);
      setCopiedMessageId(messageId);
      globalThis.window?.setTimeout(() => {
        setCopiedMessageId((currentCopiedMessageId) =>
          currentCopiedMessageId === messageId ? null : currentCopiedMessageId,
        );
      }, 1400);
    } catch {
      // Clipboard may be blocked by browser policy; keep UI silent in that case.
    }
  };

  const handleSendMessage = async () => {
    if (isSending) {
      return;
    }

    const normalizedMessage = draftMessage.trim();
    if (!normalizedMessage) {
      setComposerError("Please enter a message before sending.");
      return;
    }

    setIsSending(true);
    setComposerError(null);
    setProgressSteps([]);
    setCopiedMessageId(null);

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      markdown: normalizedMessage,
    };
    setMessages((currentMessages) => [...currentMessages, userMessage]);
    setDraftMessage("");

    if (textareaRef.current) {
      textareaRef.current.value = "";
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.overflowY = "hidden";
    }

    try {
      const streamResponse = await sendAssistantGenerateStream(
        { message: normalizedMessage },
        {
          onStatus: handleStatusEvent,
        },
      );

      setProgressSteps([]);
      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          markdown: streamResponse.markdown,
          strategyCode: streamResponse.strategy_code,
          isStrategyGeneration: streamResponse.is_strategy_generation,
        },
      ]);
    } catch (error) {
      setProgressSteps([]);
      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: `assistant-error-${Date.now()}`,
          role: "assistant",
          markdown: `**Assistant Error:** ${getErrorMessage(error)}`,
        },
      ]);
    } finally {
      setIsSending(false);

      if (globalThis.window !== undefined) {
        globalThis.window.requestAnimationFrame(() => {
          resizeTextarea();
          textareaRef.current?.focus({ preventScroll: true });
        });
      }
    }
  };

  const handleClearConversation = () => {
    if (isSending || !hasMessages) {
      return;
    }

    setMessages([]);
    setComposerError(null);
    setProgressSteps([]);
    setCopiedMessageId(null);
  };

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-[calc(1rem+env(safe-area-inset-bottom,0px))] z-50 flex justify-center px-4 sm:bottom-[calc(1.5rem+env(safe-area-inset-bottom,0px))]">
      {isExpanded ? (
        <div
          ref={expandedRef}
          className="zstar-ai-hud-compose"
          role="application"
          onMouseEnter={() => {
            if (!canHover) {
              return;
            }

            setIsHovered(true);
          }}
          onMouseLeave={() => {
            if (!canHover) {
              return;
            }

            setIsHovered(false);
          }}
          onFocusCapture={handleExpandAndFocus}
        >
          {hasConversation ? (
            <div className="zstar-ai-hud__floating-lane">
              {hasMessages ? (
                <div className="zstar-ai-hud__clear-floating">
                  <button
                    type="button"
                    className="zstar-ai-hud__clear-button"
                    onClick={handleClearConversation}
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
                                  void handleCopyStrategyCode(message.id, message.strategyCode ?? "");
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
                                  if (!message.strategyCode || !onApplyStrategyCode) {
                                    return;
                                  }
                                  onApplyStrategyCode(message.strategyCode);
                                }}
                                disabled={!onApplyStrategyCode}
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
                            <LoaderCircle
                              className="zstar-ai-hud__progress-running h-3.5 w-3.5"
                              aria-hidden="true"
                            />
                          )}
                          <span>{step.label}</span>
                        </p>
                      ))}
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          ) : null}

          {composerError ? (
            <p className="zstar-ai-hud__error" role="alert">
              {composerError}
            </p>
          ) : null}

          <div className="zstar-ai-hud__composer-shell">
            <fieldset
              className={`zstar-ai-hud zstar-ai-hud--entry ${isExpanded ? "is-expanded" : ""} ${isPinned ? "is-pinned" : ""} ${isHovered ? "is-hovered" : ""}`}
            >
              <div className="zstar-ai-hud__composer">
                <div className="zstar-ai-hud__input-wrap">
                  <textarea
                    ref={textareaRef}
                    className="zstar-ai-hud__textarea"
                    value={draftMessage}
                    rows={1}
                    spellCheck={false}
                    placeholder="Ask strategy, generate ideas, or inspect results"
                    aria-label="AI assistant prompt"
                    onChange={(event) => {
                      setDraftMessage(event.target.value);
                      resizeTextarea();
                    }}
                    onInput={resizeTextarea}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault();
                        void handleSendMessage();
                      }
                    }}
                    onClick={(event) => {
                      event.stopPropagation();
                    }}
                    onWheel={(event) => {
                      event.stopPropagation();
                    }}
                    onTouchMove={(event) => {
                      event.stopPropagation();
                    }}
                  />
                </div>
              </div>
            </fieldset>

            <button
              type="button"
              className="zstar-ai-hud__send-bubble"
              onClick={() => {
                void handleSendMessage();
              }}
              disabled={isSending || !draftMessage.trim()}
              aria-label="Send prompt"
            >
              <ArrowUp className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </div>
      ) : (
        <button
          ref={buttonRef}
          type="button"
          className={`zstar-ai-hud ${isExpanded ? "is-expanded" : ""} ${isPinned ? "is-pinned" : ""} ${isHovered ? "is-hovered" : ""}`}
          aria-expanded={isExpanded}
          aria-label="Open AI assistant"
          onMouseEnter={() => {
            if (!canHover) {
              return;
            }

            setIsHovered(true);
          }}
          onMouseLeave={() => {
            if (!canHover) {
              return;
            }

            setIsHovered(false);
          }}
          onClick={handleExpandAndFocus}
          onFocusCapture={handleExpandAndFocus}
        >
          <div className="zstar-ai-hud__collapsed">
            <span>Ask or Generate</span>
          </div>
        </button>
      )}
    </div>
  );
}
