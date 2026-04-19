"use client";

import { useEffect, useRef, useState } from "react";
import type { RefObject } from "react";

import { sendAssistantGenerateStream } from "@/features/aiAssistant/api";
import type { AssistantStatusEvent } from "@/types/aiAssistant";

import type { ChatMessage, ProgressStep } from "@/components/organisms/ai-hud/types";

const HOVER_MEDIA_QUERY = "(hover: hover) and (pointer: fine)";
const MAX_HUD_HEIGHT_RATIO = 0.7;
const MAX_TEXTAREA_HEIGHT_RATIO = 0.4;
const MIN_TEXTAREA_HEIGHT = 96;

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

function createIsEventInsideHud(
  expandedRef: RefObject<HTMLDivElement | null>,
  buttonRef: RefObject<HTMLButtonElement | null>,
): (target: EventTarget | null) => boolean {
  return (target: EventTarget | null): boolean => {
    if (!(target instanceof Node)) {
      return false;
    }

    return Boolean(expandedRef.current?.contains(target) || buttonRef.current?.contains(target));
  };
}

interface UseAIAssistantHudControllerOptions {
  readonly onApplyStrategyCode?: (code: string) => void;
}

export function useAIAssistantHudController(options: Readonly<UseAIAssistantHudControllerOptions>) {
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
    if (!strategyCode.trim() || navigator.clipboard === undefined) {
      return;
    }

    try {
      await navigator.clipboard.writeText(strategyCode);
      setCopiedMessageId(messageId);
      globalThis.window.setTimeout(() => {
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

  const applyStrategyCode = (strategyCode: string) => {
    if (!options.onApplyStrategyCode) {
      return;
    }

    options.onApplyStrategyCode(strategyCode);
  };

  return {
    refs: {
      expandedRef,
      buttonRef,
      textareaRef,
      historyRef,
    },
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
      setIsPinned,
      setDraftMessage,
      resizeTextarea,
      handleExpandAndFocus,
      handleCopyStrategyCode,
      handleSendMessage,
      handleClearConversation,
      applyStrategyCode,
    },
  };
}
