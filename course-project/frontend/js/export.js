import { initLayout, qs, toast, fmtRub } from "./app.js";

initLayout();

function loadCompare(){
  try { return JSON.parse(localStorage.getItem("compare:list") || "[]"); }
  catch { return []; }
}

function renderPreview(){
  const items = loadCompare().slice(0, 10);
  const tbody = qs("#preview");
  tbody.innerHTML = "";
  if (!items.length){
    tbody.innerHTML = `<tr><td colspan="5" style="color:var(--muted); padding:14px;">Нет данных для предпросмотра.</td></tr>`;
    return;
  }
  for (const p of items){
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${p.id}</td>
      <td>${p.name||""}</td>
      <td>${p.faculty||""}</td>
      <td>${p.level||""}</td>
      <td>${p.university_name||""}</td>
      <td>${p.city||""}</td>
      <td>${p.budget_places||""}</td>
      <td>${p.paid_places||""}</td>
      <td>${fmtRub(p.tuition_cost_rub_year||0)}</td>
      <td>${p.budget_passing_score||""}</td>
      <td>${p.paid_min_score||""}</td>
      <td>${p.duration||""}</td>
      <td>${p.study_format||""}</td>
      <td>${p.language||""}</td>
      <td>${p.accreditation||""}</td>
    `;
    tbody.appendChild(tr);
  }
}

qs("#btnExport").addEventListener("click", ()=>{
  const ds = qs("#dataset").value;
  const fmt = qs("#format").value;
  const filename = (qs("#filename").value || "export.csv").trim();

  if (ds !== "compare") return toast("В MVP доступно только сравнение");
  if (fmt !== "csv") return toast("В MVP доступен только CSV");

  const items = loadCompare();
  if (!items.length) return toast("Нет данных для экспорта");

  const cols = ["id", "name", "faculty", "level", "university_name", "city", "budget_places", "paid_places", "tuition_cost_rub_year", "budget_passing_score", "paid_min_score", "duration", "study_format", "language", "accreditation"];
  const lines = [cols.join(",")];
  for (const it of items){
    const row = cols.map(c => `"${String(it[c] ?? "").replaceAll('"','""')}"`);
    lines.push(row.join(","));
  }
  const blob = new Blob([lines.join("\n")], {type:"text/csv;charset=utf-8"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename.endsWith(".csv") ? filename : (filename + ".csv");
  a.click();
  URL.revokeObjectURL(a.href);
});

renderPreview();