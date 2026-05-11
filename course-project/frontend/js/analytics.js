import { initLayout, qs, toast } from "./app.js";
import { Api } from "./api.js";

initLayout();

function toBarFigure(series, title) {
  return {
    title,
    data: [
      {
        type: "bar",
        x: Array.isArray(series?.labels) ? series.labels : [],
        y: Array.isArray(series?.values) ? series.values : [],
        marker: {
          color: "#2f7fb7",
          line: { color: "#3f8fca", width: 1 }
        },
        hovertemplate: "%{x}<br>%{y}<extra></extra>"
      }
    ],
    layout: {
      title: { text: title, x: 0.5 },
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      font: { color: "#e5e7eb" },
      margin: { l: 50, r: 20, t: 50, b: 80 },
      xaxis: {
        tickangle: -20,
        automargin: true,
        gridcolor: "rgba(255,255,255,0.08)"
      },
      yaxis: {
        automargin: true,
        gridcolor: "rgba(255,255,255,0.14)",
        zerolinecolor: "rgba(255,255,255,0.18)"
      }
    }
  };
}

function toPieFigure(series, title) {
  return {
    title,
    data: [
      {
        type: "pie",
        labels: Array.isArray(series?.labels) ? series.labels : [],
        values: Array.isArray(series?.values) ? series.values : [],
        hole: 0.45,
        textinfo: "label+percent",
        marker: {
          colors: ["#2f7fb7", "#4ca3dd", "#7bc0ee", "#a8d8f0"]
        }
      }
    ],
    layout: {
      title: { text: title, x: 0.5 },
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      font: { color: "#e5e7eb" },
      margin: { l: 20, r: 20, t: 50, b: 20 }
    }
  };
}

function cloneRange(range) {
  return Array.isArray(range) ? [...range] : null;
}

function getCurrentAxisRange(gd, axisName) {
  const axis = gd?._fullLayout?.[axisName];
  if (!axis || !Array.isArray(axis.range)) return null;
  return [...axis.range];
}

function zoomAxis(gd, axisName, factor) {
  const current = getCurrentAxisRange(gd, axisName);
  if (!current) return null;

  const min = Number(current[0]);
  const max = Number(current[1]);
  if (!Number.isFinite(min) || !Number.isFinite(max)) return null;

  const center = (min + max) / 2;
  const half = ((max - min) / 2) * factor;
  return [center - half, center + half];
}

function bindPlotButtons(gd, fig, btnPlus, btnMinus, btnReset) {
  const initialX = cloneRange(fig?.layout?.xaxis?.range);
  const initialY = cloneRange(fig?.layout?.yaxis?.range);

  btnPlus?.addEventListener("click", () => {
    const update = {};
    const xr = zoomAxis(gd, "xaxis", 0.8);
    const yr = zoomAxis(gd, "yaxis", 0.8);

    if (xr) update["xaxis.range"] = xr;
    if (yr) update["yaxis.range"] = yr;

    if (Object.keys(update).length) Plotly.relayout(gd, update);
  });

  btnMinus?.addEventListener("click", () => {
    const update = {};
    const xr = zoomAxis(gd, "xaxis", 1.25);
    const yr = zoomAxis(gd, "yaxis", 1.25);

    if (xr) update["xaxis.range"] = xr;
    if (yr) update["yaxis.range"] = yr;

    if (Object.keys(update).length) Plotly.relayout(gd, update);
  });

  btnReset?.addEventListener("click", () => {
    const update = {
      "xaxis.autorange": true,
      "yaxis.autorange": true
    };

    if (initialX) {
      update["xaxis.range"] = initialX;
      update["xaxis.autorange"] = false;
    }
    if (initialY) {
      update["yaxis.range"] = initialY;
      update["yaxis.autorange"] = false;
    }

    Plotly.relayout(gd, update);
  });
}

function createPlotCard(fig, index) {
  const card = document.createElement("div");
  card.className = "plot-card";

  const head = document.createElement("div");
  head.className = "plot-card-head";

  const title = document.createElement("div");
  title.className = "plot-title";
  title.textContent = fig?.title || `График ${index + 1}`;

  const tools = document.createElement("div");
  tools.className = "plot-tools";

  const btnPlus = document.createElement("button");
  btnPlus.type = "button";
  btnPlus.textContent = "+";

  const btnMinus = document.createElement("button");
  btnMinus.type = "button";
  btnMinus.textContent = "−";

  const btnReset = document.createElement("button");
  btnReset.type = "button";
  btnReset.textContent = "Сброс";

  tools.appendChild(btnPlus);
  tools.appendChild(btnMinus);
  tools.appendChild(btnReset);

  head.appendChild(title);
  head.appendChild(tools);

  const frame = document.createElement("div");
  frame.className = "plot-frame";
  frame.id = `plot-${index}`;

  card.appendChild(head);
  card.appendChild(frame);

  return { card, frame, btnPlus, btnMinus, btnReset };
}

function toScatterFigure(points, title) {
  const xs = Array.isArray(points) ? points.map(p => p.x) : [];
  const ys = Array.isArray(points) ? points.map(p => p.y) : [];
  const labels = Array.isArray(points) ? points.map(p => p.label || "") : [];

  return {
    title,
    data: [
      {
        type: "scatter",
        mode: "markers",
        x: xs,
        y: ys,
        text: labels,
        hovertemplate:
          "%{text}<br>Стоимость: %{x} ₽/год<br>Бюджетных мест: %{y}<extra></extra>",
        marker: {
          color: "#4ca3dd",
          size: 9,
          line: { color: "#1f2937", width: 1 }
        }
      }
    ],
    layout: {
      title: { text: title, x: 0.5 },
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      font: { color: "#e5e7eb" },
      margin: { l: 60, r: 20, t: 50, b: 60 },
      xaxis: {
        title: "Стоимость (₽/год)",
        gridcolor: "rgba(255,255,255,0.08)"
      },
      yaxis: {
        title: "Бюджетные места",
        gridcolor: "rgba(255,255,255,0.14)",
        zerolinecolor: "rgba(255,255,255,0.18)"
      }
    }
  };
}

function buildFigures(
  summary,
  byCity,
  byFaculty,
  budgetVsPaid,
  priceBuckets,
  priceVsBudget,
  avgPriceByCity,
  levelFormat
) {
  const figures = [];

  if (byCity?.labels?.length) {
    figures.push(toBarFigure(byCity, "Программы по городам"));
  }

  if (byFaculty?.labels?.length) {
    figures.push(toBarFigure(byFaculty, "Программы по факультетам"));
  }

  if (budgetVsPaid?.labels?.length) {
    figures.push(toPieFigure(budgetVsPaid, "Бюджет vs только платное"));
  }

  if (priceBuckets?.labels?.length) {
    figures.push(
      toBarFigure(priceBuckets, "Распределение программ по диапазонам стоимости")
    );
  }

  if (Array.isArray(priceVsBudget) && priceVsBudget.length) {
    figures.push(
      toScatterFigure(
        priceVsBudget,
        "Стоимость обучения vs количество бюджетных мест"
      )
    );
  }

  if (avgPriceByCity?.labels?.length) {
    const fig = toBarFigure(
      avgPriceByCity,
      "Средняя стоимость обучения по городам (Топ-10)"
    );
    fig.layout = {
      ...fig.layout,
      xaxis: { ...(fig.layout.xaxis || {}), title: "Средняя стоимость (₽/год)" }
    };
    figures.push(fig);
  }

  if (levelFormat?.labels?.length) {
    figures.push(
      toBarFigure(
        levelFormat,
        "Распределение программ по уровню подготовки и форме обучения"
      )
    );
  }

  if (summary) {
    const labels = [];
    const values = [];

    if (typeof summary.total_programs === "number") {
      labels.push("Всего программ");
      values.push(summary.total_programs);
    }
    if (typeof summary.budget_programs === "number") {
      labels.push("С бюджетом");
      values.push(summary.budget_programs);
    }
    if (
      typeof summary.total_programs === "number" &&
      typeof summary.budget_programs === "number"
    ) {
      labels.push("Без бюджета");
      values.push(summary.total_programs - summary.budget_programs);
    }

    if (labels.length) {
      figures.push(
        toBarFigure(
          { labels, values },
          "Краткая сводка по количеству программ"
        )
      );
    }
  }

  return figures;
}

async function load() {
  try {
    const plotsEl = document.querySelector("#plots");
    if (!plotsEl) {
      console.error("Не найден #plots");
      return;
    }

    if (!window.Plotly) {
      plotsEl.innerHTML = `
        <div class="plot-card">
          <div class="plot-title">Ошибка</div>
          <div style="margin-top:8px;color:var(--muted);font-size:13px;">
            Plotly не загружен.
          </div>
        </div>
      `;
      return;
    }

    const [
      summary,
      byCity,
      byFaculty,
      budgetVsPaid,
      priceBuckets,
      priceVsBudget,
      avgPriceByCity,
      levelFormat
    ] = await Promise.all([
      Api.getAnalyticsSummary(),
      Api.getProgramsByCity({ limit: 10 }),
      Api.getProgramsByFaculty({ limit: 10 }),
      Api.getBudgetVsPaid(),
      Api.getPriceBuckets(),
      Api.getPriceVsBudget(),
      Api.getAvgPriceByCity({ limit: 10 }),
      Api.getLevelFormat()
    ]);

    const figures = buildFigures(
      summary,
      byCity,
      byFaculty,
      budgetVsPaid,
      priceBuckets,
      priceVsBudget,
      avgPriceByCity,
      levelFormat
    );

    plotsEl.innerHTML = "";

    if (!figures.length) {
      plotsEl.innerHTML = `
        <div class="plot-card">
          <div class="plot-title">Нет данных</div>
          <div style="margin-top:8px;color:var(--muted);font-size:13px;">
            Аналитика вернулась пустой.
          </div>
        </div>
      `;
      return;
    }

    figures.forEach((fig, index) => {
      const { card, frame, btnPlus, btnMinus, btnReset } = createPlotCard(fig, index);
      plotsEl.appendChild(card);

      Plotly.newPlot(
        frame,
        Array.isArray(fig?.data) ? fig.data : [],
        {
          ...(fig?.layout || {}),
          dragmode: "zoom"
        },
        {
          responsive: true,
          displayModeBar: false,
          scrollZoom: false,
          doubleClick: "reset"
        }
      )
        .then((gd) => {
          bindPlotButtons(gd, fig, btnPlus, btnMinus, btnReset);

          window.addEventListener("resize", () => {
            Plotly.Plots.resize(gd);
          });
        })
        .catch((err) => {
          console.error(`Ошибка рендера графика ${index}`, err);
          frame.innerHTML = `
          <div style="padding:16px;color:#f88;">
            Ошибка рендера графика ${index + 1}
          </div>
        `;
        });
    });
  } catch (e) {
    console.error(e);
    toast("Ошибка загрузки аналитики");

    const plotsEl = document.querySelector("#plots");
    if (plotsEl) {
      plotsEl.innerHTML = `
        <div class="plot-card">
          <div class="plot-title">Ошибка</div>
          <div style="margin-top:8px;color:var(--muted);font-size:13px;">
            Не удалось загрузить данные аналитики.
          </div>
        </div>
      `;
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const btnReload = qs("#btnReload");
  if (btnReload) btnReload.addEventListener("click", load);
  load();
});