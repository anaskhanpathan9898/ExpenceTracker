/**
 * dashboard.js
 * Sets today's date on date inputs that are empty, and other
 * small dashboard UI helpers.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Set default value for any date input that is empty
  const dateInputs = document.querySelectorAll("input[type='date']");
  const today = new Date().toISOString().split("T")[0];
  dateInputs.forEach(input => {
    if (!input.value) input.value = today;
  });
});
