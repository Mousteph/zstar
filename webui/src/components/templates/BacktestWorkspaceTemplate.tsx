"use client";

import type { ReactNode } from "react";
import type { Layout } from "react-resizable-panels";

import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/atoms/Resizable";

interface BacktestWorkspaceTemplateProps {
  readonly isDesktopLayout: boolean;
  readonly isCodeVisible: boolean;
  readonly dashboardPanelSize: number;
  readonly onHorizontalLayout: (layout: Layout) => void;
  readonly dashboardPanel: ReactNode;
  readonly editorPanel: ReactNode;
}

export function BacktestWorkspaceTemplate({
  isDesktopLayout,
  isCodeVisible,
  dashboardPanelSize,
  onHorizontalLayout,
  dashboardPanel,
  editorPanel,
}: Readonly<BacktestWorkspaceTemplateProps>) {
  if (isDesktopLayout && isCodeVisible) {
    return (
      <div className="h-full">
        <ResizablePanelGroup direction="horizontal" onLayoutChange={onHorizontalLayout}>
          <ResizablePanel defaultSize={dashboardPanelSize} minSize={24} className="flex flex-col">
            {dashboardPanel}
          </ResizablePanel>

          <ResizableHandle />

          <ResizablePanel defaultSize={100 - dashboardPanelSize} minSize={22} className="border-l border-border/80">
            {editorPanel}
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    );
  }

  if (isDesktopLayout) {
    return <section className="h-full min-h-0 overflow-hidden flex flex-col">{dashboardPanel}</section>;
  }

  if (isCodeVisible) {
    return (
      <div className="grid h-full grid-rows-[320px_minmax(0,1fr)]">
        <section className="min-h-0 border-b border-border/80">{editorPanel}</section>
        <section className="min-h-0 overflow-hidden flex flex-col">{dashboardPanel}</section>
      </div>
    );
  }

  return <section className="h-full min-h-0 overflow-hidden flex flex-col">{dashboardPanel}</section>;
}
