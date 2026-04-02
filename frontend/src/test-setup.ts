import "@testing-library/jest-dom/vitest";

// Stub CSS custom properties used by chart components (useCssVars).
// jsdom's getComputedStyle returns "" for CSS vars; charts need real values.
const root = document.documentElement;
root.style.setProperty("--chart-1", "hsl(220 70% 50%)");
root.style.setProperty("--chart-2", "hsl(160 60% 45%)");
root.style.setProperty("--chart-3", "hsl(30 80% 55%)");
root.style.setProperty("--chart-4", "hsl(280 65% 60%)");
root.style.setProperty("--chart-5", "hsl(340 75% 55%)");

// Polyfill APIs missing in jsdom that Radix UI components depend on
if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}

if (typeof globalThis.PointerEvent === "undefined") {
  globalThis.PointerEvent = class PointerEvent extends MouseEvent {
    constructor(type: string, init?: PointerEventInit) {
      super(type, init);
    }
  } as typeof globalThis.PointerEvent;
}

if (typeof Element.prototype.scrollIntoView === "undefined") {
  Element.prototype.scrollIntoView = () => {};
}

if (typeof Element.prototype.hasPointerCapture === "undefined") {
  Element.prototype.hasPointerCapture = () => false;
}

if (typeof Element.prototype.releasePointerCapture === "undefined") {
  Element.prototype.releasePointerCapture = () => {};
}
