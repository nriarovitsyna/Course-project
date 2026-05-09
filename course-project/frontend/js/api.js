import { apiUrl } from "./app.js";


async function httpGet(path, query) {
  const res = await fetch(apiUrl(path, query), {
    headers: { "Accept": "application/json" }
  });

  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${txt || res.statusText}`);
  }

  return res.json();
}


async function httpPost(path, data) {
  const res = await fetch(apiUrl(path), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json"
    },
    body: JSON.stringify(data)
  });

  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${txt || res.statusText}`);
  }

  return res.json();
}


export const Api = {
  // ===== PROGRAMS =====
  getPrograms: (params) => httpGet("/programs", params),
  getProgram: (id) => httpGet(`/programs/${id}`),
  getFilterValues: () => httpGet("/filters/values"),

  // alias, чтобы фронт мог вызывать и так тоже
  getFilterOptions: () => httpGet("/filters/values"),


  // ===== ANALYTICS =====
  getAnalyticsSummary: (params) => httpGet("/analytics/analytics/summary", params),
  getProgramsByCity: (params) => httpGet("/analytics/analytics/programs-by-city", params),
  getProgramsByFaculty: (params) => httpGet("/analytics/analytics/programs-by-faculty", params),
  getBudgetVsPaid: (params) => httpGet("/analytics/analytics/budget-vs-paid", params),


  // ===== ML =====
  smartSearch: (query, options = {}) =>
    httpPost("/ml/smart-search", {
      query,
      compatibility_threshold: options.compatibility_threshold ?? 0,
      limit: options.limit ?? 10
    }),

  analyzeText: (text) =>
    httpPost("/ml/analyze-text", { text }),

  getClusters: (data = {}) =>
    httpPost("/ml/cluster", {
      features: data.features ?? ["price", "city", "budget_passing_score", "level", "budget_places"],
      n_clusters: data.n_clusters ?? 3,
      algorithm: data.algorithm ?? "kmeans"
    }),

  predictPrice: (data) =>
    httpPost("/ml/predict-price", data),

  predictPopularity: (data) =>
    httpPost("/ml/predict-popularity", data),

  predictPassingScore: (data) =>
    httpPost("/ml/predict-passing-score", {
      city: data.city ?? null,
      faculty: data.faculty ?? null,
      level: data.level ?? null,
      budget_places: data.budget_places ?? null,
      paid_places: data.paid_places ?? null,
      price: data.price ?? null
    }),

  classifyCompetitiveness: (data) =>
    httpPost("/ml/classify-competitiveness", {
      city: data.city ?? null,
      faculty: data.faculty ?? null,
      level: data.level ?? null,
      budget_places: data.budget_places ?? null,
      paid_places: data.paid_places ?? null,
      price: data.price ?? null
    }),

  comparePrograms: (programIds) =>
    httpPost("/ml/compare", { program_ids: programIds }),

  explainResult: (programId, query) =>
    httpPost("/ml/explain", { program_id: Number(programId), query }),

  explain: (programId, query) =>
    httpPost("/ml/explain", { program_id: Number(programId), query })
};