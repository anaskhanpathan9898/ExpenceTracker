/**
 * theme.js — Functional Light/Dark Mode Manager
 * Handles:
 * - Anti-FOUC initialization
 * - Accessible sun/moon icon toggle
 * - LocalStorage persistence
 * - System preference detection (prefers-color-scheme)
 * - Custom event dispatch for Chart.js theme re-coloring
 */

(function () {
  const THEME_KEY = "expense_tracker_theme";

  // Get initial theme: localStorage > system preference > default light
  function getPreferredTheme() {
    const saved = localStorage.getItem(THEME_KEY);
    if (saved === "dark" || saved === "light") {
      return saved;
    }
    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      return "dark";
    }
    return "light";
  }

  // Apply theme to document
  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    updateToggleIcons(theme);
    // Dispatch custom event so charts can re-render with new colors
    window.dispatchEvent(new CustomEvent("themechanged", { detail: { theme } }));
  }

  // Update SVG icon inside toggle button
  function updateToggleIcons(theme) {
    const btn = document.getElementById("themeToggle");
    if (!btn) return;

    if (theme === "dark") {
      btn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      `;
      btn.setAttribute("aria-label", "Switch to light theme");
      btn.setAttribute("title", "Switch to light theme");
    } else {
      btn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
      `;
      btn.setAttribute("aria-label", "Switch to dark theme");
      btn.setAttribute("title", "Switch to dark theme");
    }
  }

  // Toggle theme
  function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme") || "light";
    const next = current === "dark" ? "light" : "dark";
    localStorage.setItem(THEME_KEY, next);
    applyTheme(next);
  }

  // Apply immediately before DOM renders to prevent flash
  const initialTheme = getPreferredTheme();
  document.documentElement.setAttribute("data-theme", initialTheme);

  // Setup listeners once DOM is ready
  document.addEventListener("DOMContentLoaded", () => {
    updateToggleIcons(initialTheme);
    const btn = document.getElementById("themeToggle");
    if (btn) {
      btn.addEventListener("click", toggleTheme);
    }

    // Listen for OS system theme changes if user hasn't explicitly set preference
    if (window.matchMedia) {
      window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
        if (!localStorage.getItem(THEME_KEY)) {
          applyTheme(e.matches ? "dark" : "light");
        }
      });
    }
  });
})();
