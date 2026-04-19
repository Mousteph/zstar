"use client";

import { ArrowUp } from "lucide-react";
import type { RefObject } from "react";

interface AIAssistantComposerProps {
  readonly textareaRef: RefObject<HTMLTextAreaElement | null>;
  readonly isExpanded: boolean;
  readonly isPinned: boolean;
  readonly isHovered: boolean;
  readonly draftMessage: string;
  readonly isSending: boolean;
  readonly composerError: string | null;
  readonly onDraftMessageChange: (value: string) => void;
  readonly onSendMessage: () => Promise<void>;
  readonly onResizeTextarea: () => void;
}

export function AIAssistantComposer({
  textareaRef,
  isExpanded,
  isPinned,
  isHovered,
  draftMessage,
  isSending,
  composerError,
  onDraftMessageChange,
  onSendMessage,
  onResizeTextarea,
}: Readonly<AIAssistantComposerProps>) {
  return (
    <>
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
                  onDraftMessageChange(event.target.value);
                  onResizeTextarea();
                }}
                onInput={onResizeTextarea}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    void onSendMessage();
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
            void onSendMessage();
          }}
          disabled={isSending || !draftMessage.trim()}
          aria-label="Send prompt"
        >
          <ArrowUp className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </>
  );
}
