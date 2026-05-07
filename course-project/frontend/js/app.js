window.APP = {
  API_BASE_URL: "http://localhost:8000",
  API_PREFIX: "/api",
  VERSION: "0.1.0",
};

export function apiUrl(path, query = {}) {
  const base = window.APP.API_BASE_URL.replace(/\/$/, "");
  const prefix = window.APP.API_PREFIX || "";
  const u = new URL(base + prefix + path);
  Object.entries(query).forEach(([k, v]) => {
    if (v === undefined || v === null || v === "") return;
    u.searchParams.set(k, String(v));
  });
  return u.toString();
}

export function qs(sel, root=document){ return root.querySelector(sel); }
export function qsa(sel, root=document){ return Array.from(root.querySelectorAll(sel)); }

export function fmtRub(n){
  const x = Number(n || 0);
  return new Intl.NumberFormat("ru-RU").format(x) + " ₽";
}
export function fmtInt(n){
  const x = Number(n || 0);
  return new Intl.NumberFormat("ru-RU").format(x);
}

export function debounce(fn, ms=250){
  let t=null;
  return (...args)=>{
    clearTimeout(t);
    t=setTimeout(()=>fn(...args), ms);
  };
}

export function toast(msg){
  const host = qs("#toast");
  if (!host) return alert(msg);
  const el = document.createElement("div");
  el.className = "item";
  el.textContent = msg;
  host.appendChild(el);
  setTimeout(()=>{ el.remove(); }, 3200);
}

export function setActiveNav(){
  const path = location.pathname.split("/").pop() || "index.html";
  qsa(".nav a").forEach(a=>{
    const href = a.getAttribute("href");
    a.classList.toggle("active", href === path);
  });
}

export function initLayout(){
  setActiveNav();
  const versionEl = qs("#appVersion");
  if (versionEl) versionEl.textContent = window.APP.VERSION;

  const sidebar = qs("#sidebar");
  const btnMenu = qs("#btnMenu");
  if (btnMenu && sidebar){
    btnMenu.addEventListener("click", ()=> sidebar.classList.toggle("open"));
  }

  const content = qs("#content");
  if (content && sidebar){
    content.addEventListener("click", ()=>{
      if (window.matchMedia("(max-width: 980px)").matches){
        sidebar.classList.remove("open");
      }
    });
  }
}