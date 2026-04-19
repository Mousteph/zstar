"use client";

import { useEffect } from "react";

import { DESKTOP_LAYOUT_QUERY } from "@/stores/useUIStore";

export function useDesktopLayoutSync(setDesktopLayout: (matches: boolean) => void): void {
  useEffect(() => {
    const mediaQueryList = globalThis.window.matchMedia(DESKTOP_LAYOUT_QUERY);

    const handleChange = (event: MediaQueryListEvent) => {
      setDesktopLayout(event.matches);
    };

    setDesktopLayout(mediaQueryList.matches);
    mediaQueryList.addEventListener("change", handleChange);

    return () => {
      mediaQueryList.removeEventListener("change", handleChange);
    };
  }, [setDesktopLayout]);
}
