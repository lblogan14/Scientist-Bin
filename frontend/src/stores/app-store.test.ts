import { beforeEach, describe, expect, it } from "vitest";
import { useAppStore } from "./app-store";

describe("useAppStore", () => {
  beforeEach(() => {
    // Reset store state between tests
    useAppStore.setState({
      sidebarOpen: true,
      theme: "light",
    });
    localStorage.clear();
    document.documentElement.classList.remove("dark", "science");
  });

  it("has correct initial state", () => {
    const state = useAppStore.getState();
    expect(state.sidebarOpen).toBe(true);
    expect(state.theme).toBe("light");
  });

  it("toggleSidebar flips sidebarOpen", () => {
    useAppStore.getState().toggleSidebar();
    expect(useAppStore.getState().sidebarOpen).toBe(false);

    useAppStore.getState().toggleSidebar();
    expect(useAppStore.getState().sidebarOpen).toBe(true);
  });

  it("setSidebarOpen sets explicit value", () => {
    useAppStore.getState().setSidebarOpen(false);
    expect(useAppStore.getState().sidebarOpen).toBe(false);

    useAppStore.getState().setSidebarOpen(true);
    expect(useAppStore.getState().sidebarOpen).toBe(true);
  });

  it("setTheme updates theme and persists to localStorage", () => {
    useAppStore.getState().setTheme("dark");
    expect(useAppStore.getState().theme).toBe("dark");
    expect(localStorage.getItem("scientist-bin-theme")).toBe("dark");
  });

  it("setTheme applies CSS class to document", () => {
    useAppStore.getState().setTheme("science");
    expect(document.documentElement.classList.contains("science")).toBe(true);

    useAppStore.getState().setTheme("light");
    expect(document.documentElement.classList.contains("science")).toBe(false);
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("setTheme to dark adds dark class", () => {
    useAppStore.getState().setTheme("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });
});
