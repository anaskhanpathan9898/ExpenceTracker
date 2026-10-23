/**
 * auth.js
 * Client-side validation for the login and register forms.
 * This runs BEFORE the form reaches the server, catching obvious errors fast.
 */

document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form");
  if (!form) return;

  form.addEventListener("submit", (e) => {
    const password = form.querySelector("#password");
    const confirm  = form.querySelector("#confirm_password");
    const email    = form.querySelector("#email");
    const username = form.querySelector("#username");

    let valid = true;

    // Clear previous client-side error highlights
    form.querySelectorAll(".input-error").forEach(el => el.classList.remove("input-error"));

    // Email basic check
    if (email && (!email.value.includes("@") || !email.value.includes("."))) {
      highlightError(email, "Please enter a valid email.");
      valid = false;
    }

    // Username length check (only on register page)
    if (username && username.value.trim().length < 3) {
      highlightError(username, "Username must be at least 3 characters.");
      valid = false;
    }

    // Password length
    if (password && password.value.length < 6) {
      highlightError(password, "Password must be at least 6 characters.");
      valid = false;
    }

    // Password match (only on register page)
    if (confirm && password && password.value !== confirm.value) {
      highlightError(confirm, "Passwords do not match.");
      valid = false;
    }

    if (!valid) e.preventDefault();
  });
});

/**
 * Add a red border and show a small error message under an input.
 */
function highlightError(input, message) {
  input.style.borderColor = "var(--clr-expense)";
  input.style.boxShadow   = "0 0 0 3px var(--clr-expense-light)";

  // Remove old error message if any
  const existing = input.parentElement.querySelector(".client-error");
  if (existing) existing.remove();

  const msg = document.createElement("span");
  msg.className = "client-error";
  msg.style.cssText = "color:#dc2626;font-size:0.8rem;margin-top:2px;";
  msg.textContent = message;
  input.parentElement.appendChild(msg);

  // Reset on input
  input.addEventListener("input", () => {
    input.style.borderColor = "";
    input.style.boxShadow   = "";
    if (msg.parentElement) msg.remove();
  }, { once: true });
}
