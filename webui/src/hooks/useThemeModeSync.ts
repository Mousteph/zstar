"use client";

import { useEffect } from "react";

import { THEME_STORAGE_KEY } from "@/stores/useUIStore";
import type { ThemeMode } from "@/types/theme";

export function useThemeModeSync(themeMode: ThemeMode): void {
  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove("dark", "light");
    root.classList.add(themeMode);

    try {
      globalThis.window.localStorage.setItem(THEME_STORAGE_KEY, themeMode);
    } catch {
      // Keep in-memory theme if storage is unavailable.
    }
  }, [themeMode]);
}
