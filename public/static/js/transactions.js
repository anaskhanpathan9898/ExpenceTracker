/**
 * transactions.js
 * Client-side helpers for the transaction list and form pages.
 */

document.addEventListener("DOMContentLoaded", () => {
  setDefaultDate();
});

/**
 * If the date field has no value, default it to today.
 */
function setDefaultDate() {
  const dateInput = document.getElementById("date");
  if (dateInput && !dateInput.value) {
    dateInput.value = new Date().toISOString().split("T")[0];
  }
}
