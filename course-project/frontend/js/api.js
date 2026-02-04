import { apiUrl } from "./app.js";

async function httpGet(path, query){
  const res = await fetch(apiUrl(path, query), {
    headers: { "Accept": "application/json" }
  });
  if (!res.ok){
    const txt = await res.text().catch(()=> "");
    throw new Error(`HTTP ${res.status}: ${txt || res.statusText}`);
  }
  return res.json();
}

export const Api = {
  getPrograms: (params) => httpGet("/programs", params),          
  getProgram: (id) => httpGet(`/programs/${id}`),                 
  getFilterValues: () => httpGet("/filters/values"),              
  getDashboard: () => httpGet("/analytics/dashboard"),            
};