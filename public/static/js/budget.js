/**
 * budget.js
 * Helpers for the budget page: default month picker to current month.
 */

document.addEventListener("DOMContentLoaded", () => {
  const monthPicker = document.querySelector("input[type='month']");
  if (monthPicker && !monthPicker.value) {
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth() + 1).padStart(2, "0");
    monthPicker.value = `${y}-${m}`;
  }
});
