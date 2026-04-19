"use client";

import type { ReactNode } from "react";
import type { Components } from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

function getCodeContent(children: ReactNode): string {
  if (typeof children === "string" || typeof children === "number") {
    return String(children).replace(/\n$/, "");
  }

  if (Array.isArray(children)) {
    return children.map((child) => getCodeContent(child)).join("").replace(/\n$/, "");
  }

  return "";
}

export function hasCodeBlock(markdown: string): boolean {
  return markdown.includes("```");
}

export const markdownComponents: Components = {
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
