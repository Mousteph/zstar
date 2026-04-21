"use client";

import { AIAssistantComposer } from "@/components/organisms/ai-hud/AIAssistantComposer";
import { AIAssistantHistory } from "@/components/organisms/ai-hud/AIAssistantHistory";
import { useAIAssistantHudController } from "@/components/organisms/ai-hud/useAIAssistantHudController";

interface AIAssistantHudProps {
  readonly onApplyStrategyCode?: (code: string) => void;
}

export function AIAssistantHud({ onApplyStrategyCode }: Readonly<AIAssistantHudProps>) {
  const {
    refs: { expandedRef, buttonRef, textareaRef, historyRef },
    state: {
      canHover,
      isHovered,
      isPinned,
      isExpanded,
      draftMessage,
      messages,
      composerError,
      isSending,
      progressSteps,
      copiedMessageId,
      hasMessages,
      hasConversation,
    },
    actions: {
      setIsHovered,
      setDraftMessage,
      resizeTextarea,
      handleExpandAndFocus,
      handleCopyStrategyCode,
      handleSendMessage,
      handleClearConversation,
      applyStrategyCode,
    },
  } = useAIAssistantHudController({ onApplyStrategyCode });

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
            <AIAssistantHistory
              messages={messages}
              progressSteps={progressSteps}
              isSending={isSending}
              hasMessages={hasMessages}
              copiedMessageId={copiedMessageId}
              historyRef={historyRef}
              onClearConversation={handleClearConversation}
              onCopyStrategyCode={handleCopyStrategyCode}
              onApplyStrategyCode={applyStrategyCode}
            />
          ) : null}

          <AIAssistantComposer
            textareaRef={textareaRef}
            isExpanded={isExpanded}
            isPinned={isPinned}
            isHovered={isHovered}
            draftMessage={draftMessage}
            isSending={isSending}
            composerError={composerError}
            onDraftMessageChange={setDraftMessage}
            onSendMessage={handleSendMessage}
            onResizeTextarea={resizeTextarea}
          />
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
