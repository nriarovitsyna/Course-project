import { initLayout, qs, toast, fmtRub } from "./app.js";

initLayout();

function loadCompare() {
  try {
    return JSON.parse(localStorage.getItem("compare:list") || "[]");
  } catch {
    return [];
  }
}

const cols = [
  "id",
  "name",
  "faculty",
  "level",
  "university_name",
  "city",
  "budget_places",
  "paid_places",
  "tuition_cost_rub_year",
  "budget_passing_score",
  "paid_min_score",
  "duration",
  "study_format",
  "language",
  "accreditation",
];

function renderPreview() {
  const items = loadCompare().slice(0, 10);
  const tbody = qs("#preview");
  tbody.innerHTML = "";

  if (!items.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="5" style="color:var(--muted); padding:14px;">
          Список сравнения пуст. Добавьте программы в каталоге.
        </td>
      </tr>`;
    return;
  }

  for (const p of items) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${p.id}</td>
      <td>${p.name}</td>
      <td>${p.faculty}</td>
      <td>${p.level}</td>
      <td>${p.university_name}</td>
      <td>${p.city}</td>
      <td>${p.budget_places}</td>
      <td>${p.paid_places}</td>
      <td>${fmtRub(p.tuition_cost_rub_year || 0)}</td>
      <td>${p.budget_passing_score}</td>
      <td>${p.paid_min_score}</td>
      <td>${p.duration}</td>
      <td>${p.study_format}</td>
      <td>${p.language}</td>
      <td>${p.accreditation}</td>
    `;
    tbody.appendChild(tr);
  }
}

/* ---------- CSV ---------- */

function exportCsv(items, filename) {
  const header = cols.join(",");
  const lines = [header];

  for (const it of items) {
    const row = cols.map((c) => {
      const val = it[c] ?? "";
      const str = String(val).replaceAll('"', '""');
      return `"${str}"`;
    });
    lines.push(row.join(","));
  }

  const blob = new Blob([lines.join("\n")], {
    type: "text/csv;charset=utf-8",
  });

  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename.endsWith(".csv") ? filename : filename + ".csv";
  a.click();
  URL.revokeObjectURL(a.href);
}

/* ---------- XLSX ---------- */

function exportXlsx(items, filename) {
  if (typeof XLSX === "undefined") {
    toast("Библиотека XLSX не подключена");
    return;
  }

  const header = cols;
  const data = items.map((it) => cols.map((c) => it[c] ?? ""));

  const wsData = [header, ...data];
  const ws = XLSX.utils.aoa_to_sheet(wsData);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Compare");

  const outName = filename.endsWith(".xlsx") ? filename : filename + ".xlsx";
  XLSX.writeFile(wb, outName);
}

/* ---------- PDF через FastAPI ---------- */

async function exportPdf(items, filename) {
  try {
    const response = await fetch("http://localhost:8000/api/export/pdf", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(items),
    });

    if (!response.ok) {
      toast("Ошибка при генерации PDF на сервере");
      return;
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename.endsWith(".pdf") ? filename : filename + ".pdf";
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    console.error(e);
    toast("Не удалось скачать PDF");
  }
}

/* ---------- Обработчик кнопки ---------- */

qs("#btnExport")?.addEventListener("click", async () => {
  const ds = qs("#dataset")?.value || "compare";
  const fmt = qs("#format")?.value || "csv";
  const filenameInput = qs("#filename")?.value || "export";
  const filename = filenameInput.trim() || "export";

  if (ds !== "compare") {
    toast("Пока поддерживается только экспорт списка сравнения (MVP)");
    return;
  }

  const items = loadCompare();
  if (!items.length) {
    toast("Нет данных для экспорта");
    return;
  }

  try {
    if (fmt === "csv") {
      exportCsv(items, filename);
    } else if (fmt === "xlsx") {
      exportXlsx(items, filename);
    } else if (fmt === "pdf") {
      await exportPdf(items, filename);
    } else {
      toast("Формат пока не поддерживается");
    }
  } catch (e) {
    console.error("Export error:", e);
    toast("Ошибка при экспорте. См. консоль.");
  }
});

renderPreview();