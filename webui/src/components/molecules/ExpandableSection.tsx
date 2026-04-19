"use client";

import type { ReactNode } from "react";
import { createPortal } from "react-dom";

import { cn } from "@/lib/utils";

interface ExpandableSectionProps {
  readonly isExpanded: boolean;
  readonly onCollapse: () => void;
  readonly title: ReactNode;
  readonly controls?: ReactNode;
  readonly children: ReactNode;
  readonly inlineClassName?: string;
  readonly expandedClassName?: string;
}

export function ExpandableSection({
  isExpanded,
  onCollapse,
  title,
  controls,
  children,
  inlineClassName,
  expandedClassName,
}: Readonly<ExpandableSectionProps>) {
  const section = (
    <section
      className={cn(
        isExpanded
          ? "fixed inset-5 z-[40010] flex min-h-0 flex-col rounded-2xl border border-border/80 bg-[var(--chart-expanded-overlay)] p-6 shadow-2xl backdrop-blur-sm"
          : "relative border-b border-border/80 px-2 pb-10 pt-2 sm:px-4 lg:px-6",
        isExpanded ? expandedClassName : inlineClassName,
      )}
    >
      <div className={cn("mb-5 flex items-center justify-between gap-3", isExpanded ? "shrink-0" : "")}> 
        <h3 className="text-2xl font-semibold tracking-tight text-foreground sm:text-[2rem]">{title}</h3>
        {controls}
      </div>
      {children}
    </section>
  );

  if (isExpanded && typeof document !== "undefined") {
    return createPortal(
      <>
        <button
          type="button"
          aria-label="Close expanded chart"
          className="fixed inset-0 z-[40000] bg-black/70 backdrop-blur-[1.5px]"
          onClick={onCollapse}
        />
        {section}
      </>,
      document.body,
    );
  }

  return section;
}
