/**
 * charts.js
 * Fetches data from the Flask API endpoints and renders
 * modern Chart.js visualizations on the dashboard page.
 *
 * Supports dynamic real-time theme switching (Light/Dark).
 */

const MONTH_NAMES = [
  "Jan","Feb","Mar","Apr","May","Jun",
  "Jul","Aug","Sep","Oct","Nov","Dec"
];

// Vibrant Fintech color palette
const CATEGORY_COLORS = [
  "#5865E8", // Indigo Accent
  "#10B981", // Emerald Green
  "#EF4444", // Rose Red
  "#F59E0B", // Amber Warning
  "#06B6D4", // Cyan
  "#8B5CF6", // Purple
  "#EC4899", // Pink
  "#64748B"  // Slate
];

let monthlyChartInstance = null;
let categoryChartInstance = null;

// Helpers to read CSS variables for charts
function getChartThemeColors() {
  const isDark = document.documentElement.getAttribute("data-theme") === "dark";
  return {
    textColor: isDark ? "#A7B0C3" : "#697386",
    gridColor: isDark ? "rgba(255, 255, 255, 0.06)" : "rgba(32, 40, 58, 0.06)",
    cardBg:    isDark ? "#191F30" : "#FFFFFF",
    borderColor: isDark ? "#2A3249" : "#FFFFFF"
  };
}

document.addEventListener("DOMContentLoaded", () => {
  renderMonthlyChart();
  renderCategoryChart();

  // Listen for theme switch events dispatched from theme.js
  window.addEventListener("themechanged", () => {
    updateChartThemes();
  });
});

function updateChartThemes() {
  const theme = getChartThemeColors();

  if (monthlyChartInstance) {
    monthlyChartInstance.options.scales.x.ticks.color = theme.textColor;
    monthlyChartInstance.options.scales.x.grid.color = theme.gridColor;
    monthlyChartInstance.options.scales.y.ticks.color = theme.textColor;
    monthlyChartInstance.options.scales.y.grid.color = theme.gridColor;
    monthlyChartInstance.options.plugins.legend.labels.color = theme.textColor;
    monthlyChartInstance.update();
  }

  if (categoryChartInstance) {
    categoryChartInstance.options.plugins.legend.labels.color = theme.textColor;
    categoryChartInstance.data.datasets[0].borderColor = theme.cardBg;
    categoryChartInstance.update();
  }
}

/* ==========================================================================
   Monthly Bar Chart — Income vs Expenses
   ========================================================================== */
async function renderMonthlyChart() {
  const canvas = document.getElementById("monthlyChart");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  canvas.style.opacity = "0.4";

  try {
    const year = new Date().getFullYear();
    const res  = await fetch(`/api/monthly-chart?year=${year}`);
    if (!res.ok) throw new Error("Failed to fetch monthly data");

    const data = await res.json();
    const incomeData  = data.map(d => d.income);
    const expenseData = data.map(d => d.expense);
    const theme = getChartThemeColors();

    if (monthlyChartInstance) {
      monthlyChartInstance.destroy();
    }

    monthlyChartInstance = new Chart(ctx, {
      type: "bar",
      data: {
        labels: MONTH_NAMES,
        datasets: [
          {
            label: "Income",
            data: incomeData,
            backgroundColor: "rgba(16, 185, 129, 0.85)",
            hoverBackgroundColor: "#10B981",
            borderRadius: 6,
            borderSkipped: false,
          },
          {
            label: "Expenses",
            data: expenseData,
            backgroundColor: "rgba(239, 68, 68, 0.85)",
            hoverBackgroundColor: "#EF4444",
            borderRadius: 6,
            borderSkipped: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
            labels: {
              color: theme.textColor,
              font: { family: "'Plus Jakarta Sans', sans-serif", weight: 600, size: 12 },
              usePointStyle: true,
              pointStyle: "circle",
              padding: 16
            }
          },
          tooltip: {
            backgroundColor: "rgba(17, 21, 34, 0.95)",
            titleFont: { family: "'Plus Jakarta Sans', sans-serif", weight: 700 },
            bodyFont: { family: "'Plus Jakarta Sans', sans-serif" },
            padding: 12,
            cornerRadius: 8,
            callbacks: {
              label: ctx => ` ${ctx.dataset.label}: ₹${ctx.parsed.y.toLocaleString('en-IN', {minimumFractionDigits: 2})}`
            }
          }
        },
        scales: {
          x: {
            grid: { color: theme.gridColor, drawBorder: false },
            ticks: { color: theme.textColor, font: { family: "'Plus Jakarta Sans', sans-serif", weight: 600, size: 11 } }
          },
          y: {
            beginAtZero: true,
            grid: { color: theme.gridColor, drawBorder: false },
            ticks: {
              color: theme.textColor,
              font: { family: "'Plus Jakarta Sans', sans-serif", weight: 600, size: 11 },
              callback: val => `₹${val.toLocaleString('en-IN')}`
            }
          }
        }
      }
    });
  } catch (err) {
    console.error("Monthly chart error:", err);
    canvas.parentElement.innerHTML =
      `<p style="color:var(--clr-text-secondary);text-align:center;padding:2rem">
         Could not load monthly chart data.
       </p>`;
  } finally {
    canvas.style.opacity = "1";
  }
}

/* ==========================================================================
   Category Doughnut Chart — Spending Breakdown
   ========================================================================== */
async function renderCategoryChart() {
  const canvas = document.getElementById("categoryChart");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  canvas.style.opacity = "0.4";

  try {
    const now   = new Date();
    const year  = now.getFullYear();
    const month = now.getMonth() + 1;
    const res   = await fetch(`/api/category-chart?year=${year}&month=${month}`);
    if (!res.ok) throw new Error("Failed to fetch category data");

    const data = await res.json();
    const theme = getChartThemeColors();

    if (data.length === 0) {
      canvas.parentElement.innerHTML =
        `<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:var(--clr-text-secondary);padding:1rem;text-align:center;">
           <span style="font-size:2rem;margin-bottom:0.5rem">📊</span>
           <p style="font-weight:600">No expense records for this month.</p>
         </div>`;
      return;
    }

    const labels = data.map(d => d._id);
    const totals = data.map(d => d.total);

    if (categoryChartInstance) {
      categoryChartInstance.destroy();
    }

    categoryChartInstance = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels,
        datasets: [{
          data: totals,
          backgroundColor: CATEGORY_COLORS.slice(0, labels.length),
          borderWidth: 3,
          borderColor: theme.cardBg,
          hoverOffset: 8,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "68%",
        plugins: {
          legend: {
            position: "right",
            labels: {
              color: theme.textColor,
              font: { family: "'Plus Jakarta Sans', sans-serif", weight: 600, size: 12 },
              usePointStyle: true,
              pointStyle: "circle",
              padding: 12
            }
          },
          tooltip: {
            backgroundColor: "rgba(17, 21, 34, 0.95)",
            padding: 12,
            cornerRadius: 8,
            titleFont: { family: "'Plus Jakarta Sans', sans-serif", weight: 700 },
            bodyFont: { family: "'Plus Jakarta Sans', sans-serif" },
            callbacks: {
              label: ctx => ` ₹${ctx.parsed.toLocaleString('en-IN', {minimumFractionDigits: 2})}`
            }
          }
        }
      }
    });
  } catch (err) {
    console.error("Category chart error:", err);
    canvas.parentElement.innerHTML =
      `<p style="color:var(--clr-text-secondary);text-align:center;padding:2rem">
         Could not load category chart data.
       </p>`;
  } finally {
    canvas.style.opacity = "1";
  }
}
