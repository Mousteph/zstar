"use client";

import { memo, useCallback, useMemo } from "react";
import Editor, { type Monaco } from "@monaco-editor/react";

import { cn } from "@/lib/utils";
import zstarLightTheme from "@/themes/Zstar-Light.json";
import tokyoNightTheme from "@/themes/Tokyo-Night.json";
import type { ThemeMode } from "@/types/theme";

interface EditorPanelProps {
  readonly code: string;
  readonly onCodeChange: (nextValue: string) => void;
  readonly themeMode: ThemeMode;
}

export const EditorPanel = memo(function EditorPanel({ code, onCodeChange, themeMode }: Readonly<EditorPanelProps>) {
  const handleEditorWillMount = useCallback((monaco: Monaco) => {
    monaco.editor.defineTheme(
      "zstar-night",
      tokyoNightTheme as Parameters<Monaco["editor"]["defineTheme"]>[1],
    );
    monaco.editor.defineTheme(
      "zstar-day",
      zstarLightTheme as Parameters<Monaco["editor"]["defineTheme"]>[1],
    );
  }, []);

  const resolvedTheme = useMemo(() => (themeMode === "dark" ? "zstar-night" : "zstar-day"), [themeMode]);

  const handleCodeUpdate = useCallback(
    (value: string | undefined) => {
      onCodeChange(value ?? "");
    },
    [onCodeChange],
  );

  return (
    <div className={cn("editor-panel-shell h-full w-full flex flex-col", themeMode === "dark" ? "editor-panel-dark" : "editor-panel-light")}>
      <div className="flex-1">
        <Editor
          height="100%"
          defaultLanguage="python"
          theme={resolvedTheme}
          beforeMount={handleEditorWillMount}
          value={code}
          onChange={handleCodeUpdate}
          options={{
            minimap: { enabled: false },
            fontSize: 13.5,
            fontFamily:
              '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
            fontLigatures: true,
            padding: { top: 14 },
            scrollBeyondLastLine: false,
            smoothScrolling: true,
            lineNumbersMinChars: 3,
            cursorSmoothCaretAnimation: "on",
            renderLineHighlight: "gutter",
            guides: {
              indentation: false,
            },
          }}
        />
      </div>
    </div>
  );
});
