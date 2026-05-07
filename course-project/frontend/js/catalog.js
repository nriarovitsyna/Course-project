import { initLayout, qs, qsa, debounce, toast, fmtRub, fmtInt } from "./app.js";
import { Api } from "./api.js";

initLayout();

const state = {
  view: "table",
  items: [],
  filtered: [],
  sortBy: "tuition_fee",
  sortDir: "asc",
  page: 1,
  pageSize: 20,
  filters: {
    city: "",
    level: "",
    faculty: "",
    university_name: "",
    duration: "",
    study_format: "",
    accreditation: "",
    price_min: "",
    price_max: "",
    is_budget: false,
  },
  q: (sessionStorage.getItem("catalog:q") || "").trim(),
  selectedProgramId: null,
};

const els = {
  tbody: qs("#tbody"),
  pagination: qs("#pagination"),
  totalInfo: qs("#totalInfo"),
  chips: qs("#chips"),
  cards: qs("#cardsBlock"),
  tableBlock: qs("#tableBlock"),
  cardsBlock: qs("#cardsBlock"),
  viewTable: qs("#viewTable"),
  viewCards: qs("#viewCards"),
  cmpCount: qs("#cmpCount"),
  search: qs("#globalSearch"),
  drawer: qs("#drawer"),
  btnFilters: qs("#btnFilters"),
  btnCloseDrawer: qs("#btnCloseDrawer"),
  fCity: qs("#fCity"),
  fLevel: qs("#fLevel"),
  fFaculty: qs("#fFaculty"),
  fUniversity: qs("#fUniversity"),
  fDuration: qs("#fDuration"),
  fStudyFormat: qs("#fStudyFormat"),
  fAccreditation: qs("#fAccreditation"),
  fMin: qs("#fMin"),
  fMax: qs("#fMax"),
  fBudget: qs("#fBudget"),
  btnApply: qs("#btnApply"),
  btnReset: qs("#btnReset"),
  btnClear: qs("#btnClear"),

  mb: qs("#mb"),
  modal: qs("#modal"),
  btnCloseModal: qs("#btnCloseModal"),
  btnAddCompare: qs("#btnAddCompare"),
  mTitle: qs("#mTitle"),
  mSub: qs("#mSub"),
  mBody: qs("#mBody"),
};

function loadCompare(){
  try { return JSON.parse(localStorage.getItem("compare:list") || "[]"); }
  catch { return []; }
}
function saveCompare(list){
  localStorage.setItem("compare:list", JSON.stringify(list));
  els.cmpCount.textContent = String(list.length);
}
function addToCompare(program){
  const list = loadCompare();
  if (list.some(x => x.id === program.id)) {
    toast("Уже добавлено в сравнение");
    return;
  }
  list.push(program);
  saveCompare(list);
  toast("Добавлено в сравнение");
}

function setView(v){
  state.view = v;
  els.viewTable.classList.toggle("primary", v==="table");
  els.viewCards.classList.toggle("primary", v==="cards");
  els.tableBlock.style.display = v==="table" ? "" : "none";
  els.cardsBlock.style.display = v==="cards" ? "" : "none";
  render();
}

function openDrawer(open=true){
  els.drawer.classList.toggle("open", open);
}
function openModal(open=true){
  els.mb.classList.toggle("open", open);
  els.modal.classList.toggle("open", open);
}
function chip(label, key){
  const d = document.createElement("div");
  d.className = "chip";
  d.innerHTML = `<span>${label}</span>`;
  const b = document.createElement("button");
  b.className = "ghost";
  b.textContent = "×";
  b.addEventListener("click", ()=>{
    if (key === "is_budget") state.filters.is_budget = false;
    else state.filters[key] = "";
    syncFiltersUI();
    applyFilters();
  });
  d.appendChild(b);
  return d;
}

function syncFiltersUI(){
  els.fCity.value = state.filters.city || "";
  els.fLevel.value = state.filters.level || "";
  els.fFaculty.value = state.filters.faculty || "";
  els.fUniversity.value = state.filters.university_name || "";
  els.fDuration.value = state.filters.duration || "";
  els.fStudyFormat.value = state.filters.study_format || "";
  els.fAccreditation.value = state.filters.accreditation || "";
  els.fMin.value = state.filters.price_min || "";
  els.fMax.value = state.filters.price_max || "";
  els.fBudget.checked = !!state.filters.is_budget;
  els.search.value = state.q;
}

function renderChips(){
  els.chips.innerHTML = "";
  const f = state.filters;
  if (f.city) els.chips.appendChild(chip(`Город: ${f.city}`, "city"));
  if (f.level) els.chips.appendChild(chip(`Уровень: ${f.level}`, "level"));
  if (f.faculty) els.chips.appendChild(chip(`Факультет: ${f.faculty}`, "faculty"));
  if (f.university_name) els.chips.appendChild(chip(`Вуз: ${f.university_name}`, "university_name"));
  if (f.duration) els.chips.appendChild(chip(`Длительность обучения: ${f.duration}`, "duration"));
  if (f.study_format) els.chips.appendChild(chip(`Форма обучения: ${f.study_format}`, "study_format"));
  if (f.accreditation) els.chips.appendChild(chip(`Аккредитация: ${f.accreditation}`, "accreditation"));
  if (f.price_min) els.chips.appendChild(chip(`Цена от: ${f.price_min}`, "price_min"));
  if (f.price_max) els.chips.appendChild(chip(`Цена до: ${f.price_max}`, "price_max"));
  if (f.is_budget) els.chips.appendChild(chip(`Только бюджет`, "is_budget"));
  if (state.q) {
    const d = chip(`Поиск: ${state.q}`, "__q");
    d.querySelector("button").addEventListener("click", ()=>{
      state.q = "";
      syncFiltersUI();
      applyFilters();
    });
    els.chips.appendChild(d);
  }
}

function sortItems(items){
  const { sortBy, sortDir } = state;
  const dir = sortDir === "asc" ? 1 : -1;
  return [...items].sort((a,b)=>{
    const av = a?.[sortBy];
    const bv = b?.[sortBy];
    if (typeof av === "number" && typeof bv === "number") return (av - bv) * dir;
    return String(av ?? "").localeCompare(String(bv ?? ""), "ru") * dir;
  });
}

function applyFilters(){
  const f = state.filters;
  let items = state.items;

  if (state.q){
    const q = state.q.toLowerCase();
    items = items.filter(x =>
      String(x.name||"").toLowerCase().includes(q) ||
      String(x.faculty||"").toLowerCase().includes(q) ||
      String(x.level||"").toLowerCase().includes(q) ||
      String(x.university_name||"").toLowerCase().includes(q) ||
      String(x.city||"").toLowerCase().includes(q) ||
      String(x.duration||"").toLowerCase().includes(q) ||
      String(x.study_format||"").toLowerCase().includes(q) ||
      String(x.language||"").toLowerCase().includes(q) ||
      String(x.accreditation||"").toLowerCase().includes(q)
    );
  }

  if (f.city) items = items.filter(x => x.city === f.city);
  if (f.level) items = items.filter(x => (x.level||"") === f.level);
  if (f.faculty) items = items.filter(x => (x.faculty || "") === f.faculty);
  if (f.university_name) items = items.filter(x => (x.university_name || "") === f.university_name);
  if (f.duration) items = items.filter(x => (x.duration || "") === f.duration);
  if (f.study_format) items = items.filter(x => (x.study_format || "") === f.study_format);
  if (f.accreditation) items = items.filter(x => (x.accreditation || "") === f.accreditation);
  if (f.is_budget) items = items.filter(x => Number(x.budget_places||0) > 0);

  const min = f.price_min !== "" ? Number(f.price_min) : null;
  const max = f.price_max !== "" ? Number(f.price_max) : null;
  if (min !== null) items = items.filter(x => Number(x.tuition_cost_rub_year||0) >= min);
  if (max !== null) items = items.filter(x => Number(x.tuition_cost_rub_year||0) <= max);

  state.filtered = sortItems(items);
  state.page = 1;

  renderChips();
  render();
}

function renderSortMarks(){
  const keys = ["name","faculty","university_name","city","level","tuition_cost_rub_year","budget_places","paid_places","budget_passing_score","paid_min_score","duration","study_format","language","accreditation"];
  keys.forEach(k=>{
    const el = qs(`#s_${k}`);
    if (!el) return;
    el.textContent = (state.sortBy === k) ? (state.sortDir === "asc" ? "▲" : "▼") : "";
  });
}

function renderTable(pageItems){
  els.tbody.innerHTML = "";
  for (const p of pageItems){
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><b>${p.name || ""}</b><div style="color:var(--muted); font-size:12px;">${p.department || ""}</div></td>
      <td>${p.faculty || ""}</td>
      <td>${p.level || ""}</td>
      <td>${p.university_name || ""}</td>
      <td>${p.city || ""}</td>
      <td>${fmtInt(p.budget_places)}</td>
      <td>${fmtInt(p.paid_places)}</td>
      <td>${fmtInt(p.tuition_cost_rub_year)}</td>
      <td>${fmtInt(p.budget_passing_score)}</td>
      <td>${fmtInt(p.paid_min_score)}</td>
      <td>${p.duration || ""}</td>
      <td>${p.study_format || ""}</td>
      <td>${p.language || ""}</td>
      <td>${p.accreditation || ""}</td>
      <td style="white-space:nowrap;">
        <button class="primary" data-act="cmp" data-id="${p.id}">+ сравнение</button>
      </td>
    `;
    els.tbody.appendChild(tr);
  }
  els.tbody.addEventListener("click", onRowAction);
}

function renderCards(pageItems){
  els.cards.innerHTML = "";
  for (const p of pageItems){
    const d = document.createElement("div");
    d.className = "card program-card";
    d.innerHTML = `
      <div class="h">${p.name || ""}</div>
      <div class="m">
        <div>Факультет: <b>${p.faculty || ""}</b></div>
        <div>Вуз: <b>${p.university_name || ""}</b></div>
        <div>Город: <b>${p.city || ""}</b></div>
        <div>Уровень: <b>${p.level || ""}</b></div>
      </div>
      <div class="actions">
        <button data-act="details" data-id="${p.id}">Детали</button>
        <button class="primary" data-act="cmp" data-id="${p.id}">+ сравнение</button>
      </div>
    `;
    els.cards.appendChild(d);
  }
  els.cards.addEventListener("click", onRowAction);
}

function renderPagination(total){
  const pages = Math.max(1, Math.ceil(total / state.pageSize));
  els.pagination.innerHTML = "";
  const mk = (n, label) => {
    const b = document.createElement("div");
    b.className = "page" + (n===state.page ? " active" : "");
    b.textContent = label ?? String(n);
    b.addEventListener("click", ()=>{
      state.page = n;
      render();
    });
    return b;
  };
  if (state.page > 1) els.pagination.appendChild(mk(state.page-1, "← Пред"));
  for (let i=1; i<=pages; i++){
    if (i===1 || i===pages || Math.abs(i-state.page)<=2){
      els.pagination.appendChild(mk(i));
    }
  }
  if (state.page < pages) els.pagination.appendChild(mk(state.page+1, "След →"));
}

function render(){
  renderSortMarks();
  const total = state.filtered.length;
  els.totalInfo.textContent = `Найдено: ${total}`;

  const start = (state.page-1) * state.pageSize;
  const end = start + state.pageSize;
  const pageItems = state.filtered.slice(start, end);

  if (state.view === "table") renderTable(pageItems);
  else renderCards(pageItems);

  renderPagination(total);
}

async function openDetails(id){
  state.selectedProgramId = id;
  openModal(true);
  els.mTitle.textContent = "Загрузка…";
  els.mSub.textContent = "";
  els.mBody.innerHTML = "";

  try{
    const p = await Api.getProgram(id);
    els.mTitle.textContent = p.name || "Программа";
    els.mSub.textContent = `${p.university_name || ""} • ${p.city || ""}`;

    const sec1 = document.createElement("div");
    sec1.className = "section";
    sec1.innerHTML = `
      <h3>Основная информация</h3>
      <div class="kv">
        <div>Факультет</div><div><b>${p.faculty || ""}</b></div>
        <div>Уровень</div><div><b>${p.level || ""}</b></div>
        <div>Форма</div><div><b>${p.study_format || ""}</b></div>
        <div>Язык</div><div><b>${p.language || ""}</b></div>
        <div>Аккредитация</div><div><b>${p.accreditation || ""}</b></div>
      </div>
    `;

    const sec2 = document.createElement("div");
    sec2.className = "section";
    sec2.innerHTML = `
      <h3>Стоимость и места</h3>
      <div class="kv">
        <div>Стоимость</div><div><b>${fmtRub(p.tuition_cost_rub_year)}</b></div>
        <div>Бюджетных мест</div><div><b>${fmtInt(p.budget_places)}</b></div>
        <div>Платных мест</div><div><b>${fmtInt(p.paid_places)}</b></div>
        <div>Проходной балл</div><div><b>${fmtInt(p.budget_passing_score)}</b></div>
        <div>Длительность</div><div><b>${p.duration}</b></div>
      </div>
    `;

    els.mBody.appendChild(sec1);
    els.mBody.appendChild(sec2);

    els.btnAddCompare.onclick = ()=> addToCompare(p);

  } catch(e){
    els.mTitle.textContent = "Ошибка";
    els.mBody.innerHTML = `<div class="section">Не удалось загрузить детали. ${String(e.message||e)}</div>`;
  }
}

function onRowAction(e){
  const btn = e.target.closest("button");
  if (!btn) return;
  const act = btn.dataset.act;
  const id = Number(btn.dataset.id || 0);
  if (!id) return;

  const p = state.items.find(x => x.id === id) || state.filtered.find(x=>x.id===id);

  if (act === "details") openDetails(id);
  if (act === "cmp" && p) addToCompare(p);
}

async function initFilters(){
  try{
    const v = await Api.getFilterValues(); 
    const cities = v.cities || v.city || v.values?.cities || [];
    els.fCity.innerHTML = `<option value="">Любой</option>` + cities.map(c=>`<option>${c}</option>`).join("");

    const levels = v.level || [];
    els.fLevel.innerHTML =
      `<option value="">Любой</option>` +
      levels.map(l => `<option>${l}</option>`).join("");

    const faculties = v.faculty || [];
    els.fFaculty.innerHTML =
      `<option value="">Любой</option>` +
      faculties.map(f => `<option>${f}</option>`).join("");

    const universities = v.university_name || [];
    els.fUniversity.innerHTML =
      `<option value="">Любой</option>` +
      universities.map(u => `<option>${u}</option>`).join("");

    const durations = v.duration || [];
    els.fDuration.innerHTML =
      `<option value="">Любая</option>` +
      durations.map(d => `<option>${d}</option>`).join("");

    const formats = v.study_format || [];
    els.fStudyFormat.innerHTML =
      `<option value="">Любая</option>` +
      formats.map(s => `<option>${s}</option>`).join("");

    const accreditations = v.accreditation || [];
    els.fAccreditation.innerHTML =
      `<option value="">Любая</option>` +
      accreditations.map(s => `<option>${s}</option>`).join("");
  } catch(e){
    toast("Не удалось загрузить значения фильтров");
  }
}

async function loadProgramsFromApi(){
  const params = {
    city: state.filters.city || null,
    price_min: state.filters.price_min !== "" ? Number(state.filters.price_min) : null,
    price_max: state.filters.price_max !== "" ? Number(state.filters.price_max) : null,
    is_budget: state.filters.is_budget ? true : null,
    level: state.filters.level || null,
  };

  const data = await Api.getPrograms(params);
  state.items = data.items || [];
  state.filtered = state.items;
}

function wire(){
  saveCompare(loadCompare());

  els.viewTable.addEventListener("click", ()=> setView("table"));
  els.viewCards.addEventListener("click", ()=> setView("cards"));

  els.btnFilters.addEventListener("click", ()=> openDrawer(true));
  els.btnCloseDrawer.addEventListener("click", ()=> openDrawer(false));

  els.btnApply.addEventListener("click", async ()=>{
    state.filters.city = els.fCity.value;
    state.filters.level = els.fLevel.value;
    state.filters.faculty = els.fFaculty.value;
    state.filters.university_name = els.fUniversity.value;
    state.filters.duration = els.fDuration.value;
    state.filters.study_format = els.fStudyFormat.value;
    state.filters.accreditation = els.fAccreditation.value;
    state.filters.price_min = els.fMin.value;
    state.filters.price_max = els.fMax.value;
    state.filters.is_budget = els.fBudget.checked;
    openDrawer(false);

    try{
      await loadProgramsFromApi();
      applyFilters();
    } catch(e){
      toast("Ошибка загрузки данных");
    }
  });

  els.btnReset.addEventListener("click", ()=>{
    state.filters = { city:"", level:"", price_min:"", price_max:"", is_budget:false };
    state.q = "";
    syncFiltersUI();
    applyFilters();
  });

  els.btnClear.addEventListener("click", ()=>{
    state.filters = { city:"", level:"", price_min:"", price_max:"", is_budget:false };
    state.q = "";
    syncFiltersUI();
    loadProgramsFromApi().then(applyFilters).catch(()=> toast("Ошибка загрузки"));
  });

  qsa("thead th[data-sort]").forEach(th=>{
    th.addEventListener("click", ()=>{
      const k = th.dataset.sort;
      if (state.sortBy === k) state.sortDir = (state.sortDir==="asc" ? "desc" : "asc");
      else { state.sortBy = k; state.sortDir = "asc"; }
      applyFilters();
    });
  });

  els.search.value = state.q;
  els.search.addEventListener("input", debounce(()=>{
    state.q = els.search.value.trim();
    applyFilters();
  }, 200));

  window.addEventListener("keydown", (e)=>{
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k"){
      e.preventDefault();
      els.search.focus();
    }
    if (e.key === "Escape"){
      openDrawer(false);
      openModal(false);
    }
  });

  els.btnCloseModal.addEventListener("click", ()=> openModal(false));
  els.mb.addEventListener("click", ()=> openModal(false));
}

(async function main(){
  wire();
  await initFilters();
  syncFiltersUI();

  try{
    await loadProgramsFromApi();
    applyFilters();
  } catch(e){
    toast("Нет данных по запросу или backend недоступен");
  }
})();