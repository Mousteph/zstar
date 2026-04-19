import { create } from "zustand";

import type { ThemeMode } from "@/types/theme";

const DESKTOP_LAYOUT_QUERY = "(min-width: 1024px)";
const THEME_STORAGE_KEY = "zstar.theme";
const DEFAULT_DASHBOARD_PANEL_SIZE = 62;

function getInitialThemeMode(): ThemeMode {
  if (typeof window === "undefined") {
    return "dark";
  }

  try {
    const persistedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
    return persistedTheme === "light" ? "light" : "dark";
  } catch {
    return "dark";
  }
}

function getInitialDesktopLayout(): boolean {
  if (typeof window === "undefined") {
    return true;
  }

  return window.matchMedia(DESKTOP_LAYOUT_QUERY).matches;
}

interface UIState {
  isSettingsOpen: boolean;
  isCodeVisible: boolean;
  dashboardPanelSize: number;
  themeMode: ThemeMode;
  isDesktopLayout: boolean;
  openSettings: () => void;
  closeSettings: () => void;
  toggleCodeVisibility: () => void;
  setDashboardPanelSize: (size: number) => void;
  toggleThemeMode: () => void;
  setDesktopLayout: (matches: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  isSettingsOpen: false,
  isCodeVisible: true,
  dashboardPanelSize: DEFAULT_DASHBOARD_PANEL_SIZE,
  themeMode: getInitialThemeMode(),
  isDesktopLayout: getInitialDesktopLayout(),
  openSettings: () => set({ isSettingsOpen: true }),
  closeSettings: () => set({ isSettingsOpen: false }),
  toggleCodeVisibility: () =>
    set((state) => ({
      isCodeVisible: !state.isCodeVisible,
    })),
  setDashboardPanelSize: (size) =>
    set({
      dashboardPanelSize: size,
    }),
  toggleThemeMode: () =>
    set((state) => ({
      themeMode: state.themeMode === "dark" ? "light" : "dark",
    })),
  setDesktopLayout: (matches) =>
    set({
      isDesktopLayout: matches,
    }),
}));

export { DESKTOP_LAYOUT_QUERY, THEME_STORAGE_KEY, DEFAULT_DASHBOARD_PANEL_SIZE };
