"use client";

import type { ComponentProps } from "react";

import { Button } from "@/components/atoms/Button";
import { cn } from "@/lib/utils";

type ActionIconButtonProps = ComponentProps<typeof Button>;

export function ActionIconButton({ className, ...props }: Readonly<ActionIconButtonProps>) {
  return (
    <Button
      variant="ghost"
      size="icon"
      className={cn("h-9 w-9 border border-border/80 bg-muted/60 text-foreground hover:bg-muted", className)}
      {...props}
    />
  );
}
