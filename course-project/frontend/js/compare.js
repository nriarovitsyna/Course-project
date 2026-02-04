import { initLayout, qs, toast, fmtRub, fmtInt } from "./app.js";

initLayout();

function loadCompare(){
  try { return JSON.parse(localStorage.getItem("compare:list") || "[]"); }
  catch { return []; }
}
function saveCompare(list){
  localStorage.setItem("compare:list", JSON.stringify(list));
}

function render(){
  const items = loadCompare();
  const tbody = qs("#cmpBody");
  tbody.innerHTML = "";

  if (!items.length){
    tbody.innerHTML = `<tr><td colspan="8" style="color:var(--muted); padding:14px;">Список сравнения пуст.</td></tr>`;
    return;
  }

  const nums = (k)=> items.map(x=>Number(x[k]||0));
  const min = (arr)=> Math.min(...arr);
  const max = (arr)=> Math.max(...arr);

  const tuition = nums("tuition_cost_rub_year");
  const minTu = min(tuition), maxTu = max(tuition);

  // бюджетные места
  const budget = nums("budget_places");
  const minBu = min(budget), maxBu = max(budget);

  // платные места
  const paid = nums("paid_places");
  const minPd = min(paid), maxPd = max(paid);

  // проходной балл на бюджет
  const passBud = nums("budget_passing_score");
  const minPaB = min(passBud), maxPaB = max(passBud);

  // проходной балл на платные
  const passPaid = nums("paid_min_score");
  const minPaP = min(passPaid), maxPaP = max(passPaid);

  for (const p of items){
    const tr = document.createElement("tr");

    const tu = Number(p.tuition_cost_rub_year||0);
    const bu = Number(p.budget_places||0);
    const pd = Number(p.paid_places||0);
    const paB = Number(p.budget_passing_score||0);
    const paP = Number(p.paid_min_score||0);

    const tdTu = `<td style="${tu===minTu?'color:var(--ok);':''}${tu===maxTu?'color:var(--danger);':''}">${fmtRub(tu)}</td>`;
    const tdBu = `<td style="${bu===maxBu?'color:var(--ok);':''}${bu===minBu?'color:var(--danger);':''}">${fmtInt(bu)}</td>`;
    const tdPd = `<td style="${pd===maxPd?'color:var(--ok);':''}${pd===minPd?'color:var(--danger);':''}">${fmtInt(pd)}</td>`;
    const tdPaB = `<td style="${paB===maxPaB?'color:var(--danger);':''}${paB===minPaB?'color:var(--ok);':''}">${fmtInt(paB)}</td>`;
    const tdPaP = `<td style="${paP===maxPaP?'color:var(--danger);':''}${paP===minPaP?'color:var(--ok);':''}">${fmtInt(paP)}</td>`;

    tr.innerHTML = `
      <td><b>${p.name||""}</b><div style="color:var(--muted); font-size:12px;">${p.faculty ||""}</div></td>
      <td>${p.university_name||""}</td>
      <td>${p.city||""}</td>
      <td>${p.level||""}</td>
      ${tdTu}
      ${tdBu}
      ${tdPd}
      ${tdPaB}
      ${tdPaP}
      <td><button class="danger" data-id="${p.id}">×</button></td>
    `;
    tbody.appendChild(tr);
  }

  tbody.addEventListener("click", (e)=>{
    const b = e.target.closest("button");
    if (!b) return;
    const id = Number(b.dataset.id||0);
    const list = loadCompare().filter(x=>x.id !== id);
    saveCompare(list);
    render();
  });
}

qs("#btnClear").addEventListener("click", ()=>{
  localStorage.removeItem("compare:list");
  toast("Сравнение очищено");
  render();
});

qs("#btnExport").addEventListener("click", ()=>{
  const items = loadCompare();
  if (!items.length) return toast("Нечего экспортировать");

  const cols = ["id","name","department","level","university_name","city","tuition_cost_rub_year","budget_passing_score","paid_min_score"];
  const lines = [];
  lines.push(cols.join(","));
  for (const it of items){
    const row = cols.map(c => `"${String(it[c] ?? "").replaceAll('"','""')}"`);
    lines.push(row.join(","));
  }
  const blob = new Blob([lines.join("\n")], {type:"text/csv;charset=utf-8"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "compare.csv";
  a.click();
  URL.revokeObjectURL(a.href);
});

render();