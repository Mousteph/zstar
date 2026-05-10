import { create } from "zustand";

import type { ThemeMode } from "@/types/theme";

const THEME_STORAGE_KEY = "zstar.theme";

function getInitialThemeMode(): ThemeMode {
  if (globalThis.window === undefined) {
    return "dark";
  }

  try {
    const persistedTheme = globalThis.window.localStorage.getItem(THEME_STORAGE_KEY);
    return persistedTheme === "light" ? "light" : "dark";
  } catch {
    return "dark";
  }
}

interface UIState {
  isSettingsOpen: boolean;
  themeMode: ThemeMode;
  openSettings: () => void;
  closeSettings: () => void;
  toggleThemeMode: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  isSettingsOpen: false,
  themeMode: getInitialThemeMode(),
  openSettings: () => set({ isSettingsOpen: true }),
  closeSettings: () => set({ isSettingsOpen: false }),
  toggleThemeMode: () =>
    set((state) => ({
      themeMode: state.themeMode === "dark" ? "light" : "dark",
    })),
}));

export { THEME_STORAGE_KEY };
