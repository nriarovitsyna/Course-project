import { initLayout, qs, toast } from "./app.js";
import { Api } from "./api.js";

initLayout();

async function load(){
  try{
    const data = await Api.getDashboard();
    qs("#raw").textContent = JSON.stringify(data, null, 2);

    const plot = data.plot || data.figure || data.chart || data.plotly || null;

    if (plot && window.Plotly){
      const d = plot.data || plot.traces || [];
      const l = plot.layout || {};
      const cfg = plot.config || { responsive: true };
      Plotly.newPlot("plot", d, { ...l, paper_bgcolor:"rgba(0,0,0,0)", plot_bgcolor:"rgba(0,0,0,0)", font:{color:"#e7ecff"} }, cfg);
    } else {
      qs("#plot").innerHTML = `<div style="color:var(--muted);">Нет plotly-данных в ответе /analytics/dashboard.</div>`;
    }

  } catch(e){
    toast("Ошибка загрузки дашборда");
    qs("#raw").textContent = String(e.message||e);
  }
}

qs("#btnReload").addEventListener("click", load);
load();