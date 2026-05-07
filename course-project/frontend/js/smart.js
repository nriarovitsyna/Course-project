import { initLayout, qs, qsa, toast, fmtRub } from "./app.js";
import { Api } from "./api.js";

initLayout();

const state = {
    results: [],
    currentQuery: "",
    filterOptions: null
};

const inputEl = qs("#ml-input");
const btnExec = qs("#ml-execute");
const resultsEl = qs("#ml-results");
const metaEl = qs("#ml-results-meta");
const thresholdEl = qs("#threshold-input");
const thresholdValueEl = qs("#threshold-value");
const limitEl = qs("#limit-select");

// ===== ПЕРЕКЛЮЧЕНИЕ ВКЛАДОК =====
function initSmartTabs() {
    const tabButtons = Array.from(document.querySelectorAll("[data-tab]"));
    const tabPanels = Array.from(document.querySelectorAll("[data-panel]"));

    if (!tabButtons.length || !tabPanels.length) return;

    function activateTab(tabName) {
        tabButtons.forEach((btn) => {
            const isActive = btn.dataset.tab === tabName;
            btn.classList.toggle("active", isActive);
            btn.setAttribute("aria-selected", isActive ? "true" : "false");
        });

        tabPanels.forEach((panel) => {
            panel.hidden = panel.dataset.panel !== tabName;
        });
    }

    tabButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            activateTab(btn.dataset.tab);
        });
    });

    activateTab("recommendations");
}

// ===== ЗАГРУЗКА ОПЦИЙ ФИЛЬТРОВ =====
async function loadFilterOptions() {
    try {
        const v = await Api.getFilterValues();

        state.filterOptions = {
            cities: Array.isArray(v?.cities) ? v.cities : (Array.isArray(v?.city) ? v.city : []),
            levels: Array.isArray(v?.levels) ? v.levels : (Array.isArray(v?.level) ? v.level : []),
            universities: Array.isArray(v?.university_names)
                ? v.university_names
                : (Array.isArray(v?.universities)
                    ? v.universities
                    : (Array.isArray(v?.university_name) ? v.university_name : []))
        };

        populateFilterSelects();
    } catch (e) {
        console.error("Ошибка загрузки опций фильтров:", e);
        toast("Не удалось загрузить значения фильтров");
    }
}

function fillSelect(selectEl, items, emptyLabel = "Не указан") {
    if (!selectEl) return;
    const safeItems = Array.isArray(items) ? items : [];
    selectEl.innerHTML =
        `<option value="">${emptyLabel}</option>` +
        safeItems.map(item => `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`).join("");
}

function populateFilterSelects() {
    if (!state.filterOptions) return;

    fillSelect(qs("#predict-city"), state.filterOptions.cities, "Не указан");
    fillSelect(qs("#predict-level"), state.filterOptions.levels, "Не указан");
    fillSelect(qs("#predict-university"), state.filterOptions.universities, "Не указан");

    fillSelect(qs("#classify-city"), state.filterOptions.cities, "Не указан");
    fillSelect(qs("#classify-level"), state.filterOptions.levels, "Не указан");
    fillSelect(qs("#classify-university"), state.filterOptions.universities, "Не указан");
}

// ===== РЕКОМЕНДАЦИИ =====
if (thresholdEl && thresholdValueEl) {
    thresholdEl.addEventListener("input", () => {
        thresholdValueEl.textContent = `${thresholdEl.value}%`;
    });
}

if (btnExec && inputEl && resultsEl && metaEl && limitEl) {
    btnExec.addEventListener("click", async () => {
        const val = inputEl.value.trim();
        if (!val) {
            toast("Введите описание для анализа");
            return;
        }

        state.currentQuery = val;

        const userLimit = Number(limitEl.value);
        const threshold = thresholdEl ? Number(thresholdEl.value) / 100 : 0;

        btnExec.disabled = true;
        btnExec.textContent = "Поиск...";
        resultsEl.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:40px;">Загрузка...</div>`;
        metaEl.textContent = "";

        try {
            const backendLimit = Math.max(userLimit * 3, 50);

            const data = await Api.smartSearch(val, {
                compatibility_threshold: 0,
                limit: backendLimit
            });

            const allItems = data.items || [];
            const filteredItems = allItems.filter(item => (item.score ?? 0) >= threshold);
            state.results = filteredItems.slice(0, userLimit);

            renderCards(state.results);

            if (!allItems.length) {
                metaEl.textContent = "По запросу ничего не найдено";
            } else if (!filteredItems.length) {
                metaEl.textContent = `Поиск нашёл ${allItems.length} программ, но ни одна не прошла порог ${Math.round(threshold * 100)}%. Попробуйте снизить порог.`;
            } else {
                metaEl.textContent = `Показано ${state.results.length} из ${allItems.length} найденных программ • порог совместимости: ${Math.round(threshold * 100)}%`;
            }
        } catch (e) {
            console.error(e);
            toast("Ошибка: " + e.message);
            resultsEl.innerHTML = `
                <div style="grid-column:1/-1; text-align:center; padding:40px; color:var(--muted);">
                    Не удалось выполнить поиск
                </div>
            `;
        } finally {
            btnExec.disabled = false;
            btnExec.textContent = "Найти программы";
        }
    });
}

function getScoreColor(scorePercent) {
    if (scorePercent >= 80) {
        return {
            border: "#22c55e",
            badge: "rgba(34, 197, 94, 0.18)",
            text: "#86efac"
        };
    }
    if (scorePercent >= 50) {
        return {
            border: "#f59e0b",
            badge: "rgba(245, 158, 11, 0.18)",
            text: "#fcd34d"
        };
    }
    return {
        border: "#ef4444",
        badge: "rgba(239, 68, 68, 0.18)",
        text: "#fca5a5"
    };
}

function renderCards(items) {
    if (!resultsEl) return;

    if (!items.length) {
        resultsEl.innerHTML = `
            <div style="grid-column:1/-1; text-align:center; padding:40px; color:var(--muted);">
                Ничего не найдено при выбранном пороге совместимости
            </div>
        `;
        return;
    }

    resultsEl.innerHTML = items.map(item => {
        const score = item.score != null ? Math.round(item.score * 100) : 0;
        const colors = getScoreColor(score);

        return `
        <div class="card" style="
            padding:16px;
            display:flex;
            flex-direction:column;
            gap:10px;
            background:rgba(255,255,255,0.03);
            border:1px solid ${colors.border};
            box-shadow: 0 0 0 1px rgba(255,255,255,0.02) inset;
        ">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px;">
                <div style="font-weight:650; color:var(--accent); font-size:15px;">
                    ${escapeHtml(item.name || "Без названия")}
                </div>
                <div style="
                    padding:6px 10px;
                    border-radius:999px;
                    background:${colors.badge};
                    color:${colors.text};
                    font-size:12px;
                    font-weight:700;
                    white-space:nowrap;
                ">
                    ${score}%
                </div>
            </div>

            <div style="font-size:12px; color:var(--muted);">
                ${escapeHtml(item.university_name || "Университет не указан")} • ${escapeHtml(item.city || "Город не указан")}
            </div>

            <div style="
                font-size:13px;
                line-height:1.5;
                color:var(--text);
                background:rgba(0,0,0,0.16);
                padding:10px 12px;
                border-radius:10px;
            ">
                ${escapeHtml(item.explanation || (item.description ? item.description.substring(0, 140) + "..." : "Нет описания"))}
            </div>

            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px;">
                <div style="font-weight:600; font-size:14px;">
                    ${item.price > 0 ? fmtRub(item.price) : "Бюджет / бесплатно"}
                </div>
                <div style="font-size:12px; color:var(--muted);">
                    ${escapeHtml(item.level || "—")} • ${escapeHtml(item.study_format || "—")}
                </div>
            </div>

            <div style="display:flex; gap:8px; margin-top:8px;">
                <button class="primary btn-details" data-id="${item.id}" style="flex:1; font-size:12px; padding:6px;">
                    Детали
                </button>
                <button class="ghost btn-why" data-id="${item.id}" style="flex:1; font-size:12px; padding:6px;">
                    Пояснение
                </button>
            </div>
        </div>
        `;
    }).join("");

    qsa(".btn-details").forEach(btn => {
        btn.onclick = () => showDetails(btn.dataset.id);
    });

    qsa(".btn-why").forEach(btn => {
        btn.onclick = () => showWhy(btn.dataset.id);
    });
}

async function showDetails(id) {
    try {
        const p = await Api.getProgram(id);

        const mTitle = qs("#mTitle");
        const mSub = qs("#mSub");
        const mDetails = qs("#mDetails");
        const mb = qs("#mb");
        const modal = qs("#modal");

        if (!mTitle || !mSub || !mDetails || !mb || !modal) return;

        mTitle.textContent = p.name || "Программа";
        mSub.textContent = `${p.university_name || "Не указан вуз"} • ${p.city || "Не указан город"}`;
        mDetails.innerHTML = `
            <div class="section">
                <h3>Основная информация</h3>
                <div class="kv">
                    <div>Университет</div><div><b>${escapeHtml(p.university_name || "Не указано")}</b></div>
                    <div>Город</div><div><b>${escapeHtml(p.city || "Не указано")}</b></div>
                    <div>Факультет</div><div><b>${escapeHtml(p.faculty || "Не указано")}</b></div>
                    <div>Уровень</div><div><b>${escapeHtml(p.level || "Не указано")}</b></div>
                    <div>Форма обучения</div><div><b>${escapeHtml(p.study_format || "Не указано")}</b></div>
                    <div>Язык</div><div><b>${escapeHtml(p.language || "Не указано")}</b></div>
                    <div>Аккредитация</div><div><b>${escapeHtml(p.accreditation || "Не указано")}</b></div>
                    <div>Длительность</div><div><b>${escapeHtml(p.duration || "Не указано")}</b></div>
                </div>
            </div>

            <div class="section">
                <h3>Стоимость и места</h3>
                <div class="kv">
                    <div>Стоимость</div><div><b>${p.price > 0 ? fmtRub(p.price) : "Бюджет / бесплатно"}</b></div>
                    <div>Бюджетных мест</div><div><b>${p.budget_places != null ? p.budget_places : "Не указано"}</b></div>
                    <div>Платных мест</div><div><b>${p.paid_places != null ? p.paid_places : "Не указано"}</b></div>
                    <div>Проходной балл</div><div><b>${p.budget_passing_score != null ? p.budget_passing_score : "Не указано"}</b></div>
                </div>
            </div>

            ${
                p.description
                    ? `
                    <div class="section">
                        <h3>Описание программы</h3>
                        <div style="line-height:1.6; color:var(--text);">
                            ${escapeHtml(p.description)}
                        </div>
                    </div>
                    `
                    : ""
            }
        `;

        mb.classList.add("active");
        modal.classList.add("open");
    } catch (e) {
        console.error(e);
        toast("Ошибка загрузки деталей");
    }
}

async function showWhy(id) {
    try {
        const data = await Api.explain(id, state.currentQuery);

        const mTitle = qs("#mTitle");
        const mSub = qs("#mSub");
        const mDetails = qs("#mDetails");
        const mb = qs("#mb");
        const modal = qs("#modal");

        if (!mTitle || !mSub || !mDetails || !mb || !modal) return;

        mTitle.textContent = "Объяснение рекомендации";
        mSub.textContent = "";
        mDetails.innerHTML = `
            <div style="display:grid; gap:12px;">
                <div style="font-size:18px; font-weight:700; color:var(--accent);">
                    Совместимость: ${data.match_score != null ? Math.round(data.match_score * 100) + "%" : "—"}
                </div>
                <div style="font-size:14px; line-height:1.55;">
                    ${escapeHtml(data.explanation || "Объяснение недоступно")}
                </div>
            </div>
        `;

        mb.classList.add("active");
        modal.classList.add("open");
    } catch (e) {
        console.error(e);
        toast("Ошибка загрузки объяснения");
    }
}

const closeModalBtn = qs("#btnCloseModal");
if (closeModalBtn) {
    closeModalBtn.onclick = () => {
        const mb = qs("#mb");
        const modal = qs("#modal");
        if (mb) mb.classList.remove("active");
        if (modal) modal.classList.remove("open");
    };
}

// ===== КЛАСТЕРНЫЙ АНАЛИЗ =====
const clusterCountEl = qs("#cluster-count");
const clusterCountValueEl = qs("#cluster-count-value");
const clusterAlgorithmEl = qs("#cluster-algorithm");
const clusterExecuteBtn = qs("#cluster-execute");
const clusterResultsMetaEl = qs("#cluster-results-meta");
const clusterMetricsEl = qs("#cluster-metrics");
const clusterSummariesEl = qs("#cluster-summaries");
const clusterItemsEl = qs("#cluster-items");

if (clusterCountEl && clusterCountValueEl) {
    clusterCountEl.addEventListener("input", () => {
        clusterCountValueEl.textContent = clusterCountEl.value;
    });
}

if (clusterExecuteBtn) {
    clusterExecuteBtn.addEventListener("click", async () => {
        const featureCheckboxes = qsa("#cluster-features input[type='checkbox']:checked");
        const selectedFeatures = Array.from(featureCheckboxes).map(cb => cb.value);

        if (selectedFeatures.length === 0) {
            toast("Выберите хотя бы один признак для кластеризации");
            return;
        }

        const nClusters = Number(clusterCountEl?.value || 3);

        clusterExecuteBtn.disabled = true;
        clusterExecuteBtn.textContent = "Кластеризация...";
        if (clusterResultsMetaEl) clusterResultsMetaEl.textContent = "Загрузка...";
        if (clusterMetricsEl) clusterMetricsEl.style.display = "none";
        if (clusterSummariesEl) clusterSummariesEl.innerHTML = "";
        if (clusterItemsEl) clusterItemsEl.innerHTML = "";

        try {
            const data = await Api.getClusters({
                features: selectedFeatures,
                n_clusters: nClusters,
                algorithm: clusterAlgorithmEl?.value || "kmeans"
            });

            renderClusterResults(data);
        } catch (e) {
            console.error(e);
            toast("Ошибка кластеризации: " + e.message);
            if (clusterResultsMetaEl) {
                clusterResultsMetaEl.textContent = "Не удалось выполнить кластеризацию";
            }
        } finally {
            clusterExecuteBtn.disabled = false;
            clusterExecuteBtn.textContent = "Выполнить кластеризацию";
        }
    });
}

function renderClusterResults(data) {
    if (!clusterResultsMetaEl || !clusterSummariesEl || !clusterItemsEl || !clusterMetricsEl) return;

    clusterResultsMetaEl.textContent = `
        Найдено ${data.cluster_count} кластеров •
        Всего программ: ${data.items?.length || 0} •
        Алгоритм: ${formatClusterAlgorithm(data.algorithm)} •
        Признаки: ${formatFeatureLabels(data.features_used)}
    `;

    if (data.metrics) {
        const m = data.metrics;
        clusterMetricsEl.innerHTML = `
            <div class="card" style="padding: 16px;">
                <h3 style="margin-bottom: 12px; color: var(--accent);">Метрики качества кластеризации</h3>
                <div style="display: grid; gap: 8px; font-size: 14px;">
                    ${m.silhouette_score != null ? `<div>Silhouette Score: <b>${m.silhouette_score.toFixed(3)}</b> ${getSilhouetteLabel(m.silhouette_score)}</div>` : ""}
                    ${m.calinski_harabasz_score != null ? `<div>Calinski-Harabasz Index: <b>${m.calinski_harabasz_score.toFixed(2)}</b></div>` : ""}
                    ${m.davies_bouldin_score != null ? `<div>Davies-Bouldin Index: <b>${m.davies_bouldin_score.toFixed(3)}</b> ${getDBLabel(m.davies_bouldin_score)}</div>` : ""}
                </div>
            </div>
        `;
        clusterMetricsEl.style.display = "block";
    }

    if (data.clusters && data.clusters.length > 0) {
        clusterSummariesEl.innerHTML = data.clusters.map(cluster => {
            const colors = getClusterColor(cluster.cluster_id);
            return `
                <div class="card" style="
                    padding: 16px;
                    border-left: 4px solid ${colors.border};
                    background: ${colors.bg};
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; gap: 12px;">
                        <h3 style="color: ${colors.text}; margin: 0;">Кластер ${Number(cluster.cluster_id) + 1}</h3>
                        <div style="
                            padding: 4px 12px;
                            border-radius: 999px;
                            background: ${colors.badge};
                            color: ${colors.text};
                            font-size: 12px;
                            font-weight: 700;
                            white-space: nowrap;
                        ">
                            ${cluster.size} программ
                        </div>
                    </div>
                    <div style="font-size: 14px; line-height: 1.5; color: var(--text); margin-bottom: 12px;">
                        ${escapeHtml(cluster.description || "")}
                    </div>
                    ${renderClusterStats(cluster.stats)}
                </div>
            `;
        }).join("");
    }

    if (data.items && data.items.length > 0) {
        const groupedByCluster = {};
        data.items.forEach(item => {
            const key = Number(item.cluster_id);
            if (!groupedByCluster[key]) groupedByCluster[key] = [];
            groupedByCluster[key].push(item);
        });

        clusterItemsEl.innerHTML = Object.entries(groupedByCluster)
            .sort(([a], [b]) => Number(a) - Number(b))
            .map(([clusterId, items]) => {
                const colors = getClusterColor(Number(clusterId));
                return `
                    <details class="card" style="padding: 16px;">
                        <summary style="
                            cursor: pointer;
                            font-weight: 600;
                            font-size: 15px;
                            color: ${colors.text};
                            list-style: none;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            gap: 12px;
                        ">
                            <span>Программы кластера ${Number(clusterId) + 1}</span>
                            <span style="color: var(--muted); font-size: 13px;">${items.length} программ</span>
                        </summary>
                        <div style="margin-top: 12px; display: grid; gap: 10px;">
                            ${items.map(item => `
                                <div style="
                                    padding: 12px 14px;
                                    background: rgba(255, 255, 255, 0.03);
                                    border-radius: 10px;
                                    border: 1px solid rgba(255,255,255,0.06);
                                    display: flex;
                                    justify-content: space-between;
                                    align-items: center;
                                    gap: 12px;
                                    flex-wrap: wrap;
                                ">
                                    <div style="display:grid; gap:4px; min-width: 220px;">
                                        <div style="font-size: 14px; font-weight: 700; color: var(--text);">${escapeHtml(item.program_name || "Без названия")}</div>
                                        <div style="font-size: 12px; color: var(--muted);">${escapeHtml(item.university_name || "Университет не указан")} • ${escapeHtml(item.city || "Город не указан")}</div>
                                    </div>
                                    <button class="ghost btn-cluster-details" type="button" data-id="${item.program_id}" style="padding: 8px 14px; font-size: 12px;">
                                        Детали
                                    </button>
                                </div>
                            `).join("")}
                        </div>
                    </details>
                `;
            }).join("");

        qsa(".btn-cluster-details").forEach(btn => {
            btn.onclick = () => showDetails(btn.dataset.id);
        });
    }
}

function renderClusterStats(stats) {
    if (!stats) return "";

    const items = [];

    if (stats.price_mean != null) {
        items.push(`<div>Средняя стоимость: <b>${fmtRub(stats.price_mean)}</b></div>`);
    }
    if (stats.budget_passing_score_mean != null) {
        items.push(`<div>Средний проходной балл: <b>${stats.budget_passing_score_mean.toFixed(1)}</b></div>`);
    }
    if (stats.budget_places_mean != null) {
        items.push(`<div>Среднее число бюджетных мест: <b>${stats.budget_places_mean.toFixed(1)}</b></div>`);
    }
    if (stats.duration_mean != null) {
        items.push(`<div>Средняя продолжительность: <b>${stats.duration_mean.toFixed(1)} лет</b></div>`);
    }
    if (stats.city_mode) {
        items.push(`<div>Город (чаще всего): <b>${escapeHtml(stats.city_mode)}</b></div>`);
    }
    if (stats.level_mode) {
        items.push(`<div>Уровень (чаще всего): <b>${escapeHtml(stats.level_mode)}</b></div>`);
    }
    if (stats.study_format_mode) {
        items.push(`<div>Форма обучения: <b>${escapeHtml(stats.study_format_mode)}</b></div>`);
    }

    return items.length > 0
        ? `<div style="display: grid; gap: 6px; font-size: 13px; color: var(--muted);">${items.join("")}</div>`
        : "";
}

function formatClusterAlgorithm(algorithm) {
    if (algorithm === "agglomerative") return "Agglomerative Clustering";
    if (algorithm === "kmeans") return "K-Means";
    return algorithm || "—";
}

function formatFeatureLabels(features) {
    const labels = {
        name: "Название программы",
        price: "Стоимость обучения",
        city: "Город",
        budget_passing_score: "Проходной балл",
        level: "Уровень образования",
        budget_places: "Количество бюджетных мест",
        study_format: "Форма обучения",
        duration: "Продолжительность"
    };

    return Array.isArray(features) && features.length
        ? features.map(f => labels[f] || f).join(", ")
        : "—";
}

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function getClusterColor(clusterId) {
    const palette = [
        { border: "#22c55e", bg: "rgba(34, 197, 94, 0.08)", badge: "rgba(34, 197, 94, 0.18)", text: "#86efac" },
        { border: "#3b82f6", bg: "rgba(59, 130, 246, 0.08)", badge: "rgba(59, 130, 246, 0.18)", text: "#93c5fd" },
        { border: "#f59e0b", bg: "rgba(245, 158, 11, 0.08)", badge: "rgba(245, 158, 11, 0.18)", text: "#fcd34d" },
        { border: "#ef4444", bg: "rgba(239, 68, 68, 0.08)", badge: "rgba(239, 68, 68, 0.18)", text: "#fca5a5" },
        { border: "#8b5cf6", bg: "rgba(139, 92, 246, 0.08)", badge: "rgba(139, 92, 246, 0.18)", text: "#c4b5fd" },
        { border: "#ec4899", bg: "rgba(236, 72, 153, 0.08)", badge: "rgba(236, 72, 153, 0.18)", text: "#f9a8d4" },
        { border: "#06b6d4", bg: "rgba(6, 182, 212, 0.08)", badge: "rgba(6, 182, 212, 0.18)", text: "#67e8f9" },
        { border: "#14b8a6", bg: "rgba(20, 184, 166, 0.08)", badge: "rgba(20, 184, 166, 0.18)", text: "#5eead4" },
    ];
    return palette[clusterId % palette.length];
}

function getSilhouetteLabel(score) {
    if (score >= 0.7) return "(отлично)";
    if (score >= 0.5) return "(хорошо)";
    if (score >= 0.25) return "(средне)";
    return "(слабо)";
}

function getDBLabel(score) {
    if (score <= 0.5) return "(отлично)";
    if (score <= 1.0) return "(хорошо)";
    if (score <= 1.5) return "(средне)";
    return "(слабо)";
}

// ===== ПРОГНОЗИРОВАНИЕ =====
const predictExecuteBtn = qs("#predict-execute");
const predictResultEl = qs("#predict-result");

if (predictExecuteBtn && predictResultEl) {
    predictExecuteBtn.addEventListener("click", async () => {
        const city = qs("#predict-city")?.value || null;
        const level = qs("#predict-level")?.value || null;
        const universityName = qs("#predict-university")?.value || null;
        const duration = Number(qs("#predict-duration")?.value) || null;
        const budgetPlaces = Number(qs("#predict-budget-places")?.value) || null;
        const paidPlaces = Number(qs("#predict-paid-places")?.value) || null;
        const price = Number(qs("#predict-price")?.value) || null;

        predictExecuteBtn.disabled = true;
        predictExecuteBtn.textContent = "Вычисление...";
        predictResultEl.innerHTML = `<div style="text-align:center; padding:20px; color:var(--muted);">Загрузка...</div>`;

        try {
            const data = await Api.predictPassingScore({
                city,
                level,
                duration,
                university_name: universityName,
                budget_places: budgetPlaces,
                paid_places: paidPlaces,
                price
            });

            renderPredictResult(data);
        } catch (e) {
            console.error(e);
            toast("Ошибка предсказания: " + e.message);
            predictResultEl.innerHTML = `
                <div class="card" style="padding: 20px; text-align: center; color: var(--muted);">
                    Не удалось выполнить предсказание
                </div>
            `;
        } finally {
            predictExecuteBtn.disabled = false;
            predictExecuteBtn.textContent = "Предсказать балл";
        }
    });
}

function renderPredictResult(data) {
    if (!predictResultEl) return;

    const score = data.predicted_score || 0;
    const confidence = data.confidence_interval || "—";
    const metrics = data.model_metrics || {};
    const details = data.details || {};

    predictResultEl.innerHTML = `
        <div class="card" style="padding: 24px; background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(59, 130, 246, 0.1));">
            <div style="text-align: center; margin-bottom: 20px;">
                <div style="font-size: 14px; color: var(--muted); margin-bottom: 8px;">
                    Прогнозируемый проходной балл
                </div>
                <div style="font-size: 48px; font-weight: 700; color: var(--accent);">
                    ${Number(score).toFixed(1)}
                </div>
                <div style="font-size: 13px; color: var(--muted); margin-top: 4px;">
                    Доверительный интервал: ${escapeHtml(confidence)}
                </div>
            </div>

            <div style="border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 16px; margin-top: 16px;">
                <h4 style="margin-bottom: 12px; font-size: 14px; color: var(--accent);">Метрики модели</h4>
                <div style="display: grid; gap: 8px; font-size: 13px;">
                    ${metrics.mae != null ? `<div>Средняя абсолютная ошибка (MAE): <b>${metrics.mae.toFixed(2)} баллов</b></div>` : ""}
                    ${metrics.r2_score != null ? `<div>R² (объяснённая дисперсия): <b>${metrics.r2_score.toFixed(3)}</b></div>` : ""}
                    ${metrics.train_size != null ? `<div>Размер обучающей выборки: <b>${metrics.train_size} программ</b></div>` : ""}
                    ${metrics.test_size != null ? `<div>Размер тестовой выборки: <b>${metrics.test_size} программ</b></div>` : ""}
                    ${Array.isArray(metrics.features) ? `<div>Признаки: <b>${metrics.features.map(escapeHtml).join(", ")}</b></div>` : ""}
                </div>
            </div>

            ${details.interpretation ? `
                <div style="border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 16px; margin-top: 16px;">
                    <h4 style="margin-bottom: 8px; font-size: 14px; color: var(--accent);">Интерпретация</h4>
                    <div style="font-size: 13px; line-height: 1.5; color: var(--text);">
                        ${escapeHtml(details.interpretation)}
                    </div>
                </div>
            ` : ""}

            <div style="margin-top: 16px; font-size: 12px; color: var(--muted); text-align: center;">
                Модель: ${escapeHtml(data.model_name || "RandomForestRegressor")}
            </div>
        </div>
    `;
}

// ===== КЛАССИФИКАЦИЯ =====
const classifyExecuteBtn = qs("#classify-execute");
const classifyResultEl = qs("#classify-result");

function getNullableNumber(selector) {
    const value = qs(selector)?.value?.trim();
    if (value === "" || value == null) return null;

    const num = Number(value);
    return Number.isFinite(num) ? num : null;
}

if (classifyExecuteBtn && classifyResultEl) {
    classifyExecuteBtn.addEventListener("click", async () => {
        const city = qs("#classify-city")?.value || null;
        const level = qs("#classify-level")?.value || null;
        const universityName = qs("#classify-university")?.value || null;

        const duration = getNullableNumber("#classify-duration");
        const budgetPlaces = getNullableNumber("#classify-budget-places");
        const paidPlaces = getNullableNumber("#classify-paid-places");
        const price = getNullableNumber("#classify-price");
        const budgetPassingScore = getNullableNumber("#classify-budget-passing-score");

        classifyExecuteBtn.disabled = true;
        classifyExecuteBtn.textContent = "Классификация...";
        classifyResultEl.innerHTML = `<div style="text-align:center; padding:20px; color:var(--muted);">Загрузка...</div>`;

        try {
            const data = await Api.classifyCompetitiveness({
                city,
                level,
                duration,
                university_name: universityName,
                budget_places: budgetPlaces,
                paid_places: paidPlaces,
                price,
                budget_passing_score: budgetPassingScore
            });

            renderClassifyResult(data);
        } catch (e) {
            console.error(e);
            toast("Ошибка классификации: " + e.message);
            classifyResultEl.innerHTML = `
                <div class="card" style="padding: 20px; text-align: center; color: var(--muted);">
                    Не удалось выполнить классификацию
                </div>
            `;
        } finally {
            classifyExecuteBtn.disabled = false;
            classifyExecuteBtn.textContent = "Классифицировать";
        }
    });
}

function renderClassifyResult(data) {
    if (!classifyResultEl) return;

    const category = data.category || "Не определено";
    const probabilities = data.probabilities || {};
    const accuracy = data.accuracy != null ? data.accuracy : null;
    const modelMetrics = data.model_metrics || {};
    const details = data.details || {};

    const categoryColors = {
        "Доступная": { color: "#22c55e", bg: "rgba(34, 197, 94, 0.15)" },
        "Стандартная": { color: "#f59e0b", bg: "rgba(245, 158, 11, 0.15)" },
        "Высококонкурентная": { color: "#ef4444", bg: "rgba(239, 68, 68, 0.15)" }
    };

    const colors = categoryColors[category] || { color: "#6b7280", bg: "rgba(107, 114, 128, 0.15)" };

    classifyResultEl.innerHTML = `
        <div class="card" style="padding: 24px; background: linear-gradient(135deg, ${colors.bg}, rgba(59, 130, 246, 0.1));">
            <div style="text-align: center; margin-bottom: 20px;">
                <div style="font-size: 14px; color: var(--muted); margin-bottom: 8px;">
                    Категория конкурентоспособности
                </div>
                <div style="
                    display: inline-block;
                    padding: 12px 24px;
                    border-radius: 12px;
                    background: ${colors.bg};
                    border: 2px solid ${colors.color};
                    color: ${colors.color};
                    font-size: 24px;
                    font-weight: 700;
                    margin-bottom: 16px;
                ">
                    ${escapeHtml(category)}
                </div>
            </div>

            <div style="border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 16px; margin-top: 16px;">
                <h4 style="margin-bottom: 12px; font-size: 14px; color: var(--accent);">Вероятности</h4>
                <div style="display: grid; gap: 10px;">
                    ${Object.entries(probabilities).map(([cat, prob]) => {
                        const catColors = categoryColors[cat] || { color: "#6b7280", bg: "rgba(107, 114, 128, 0.15)" };
                        return `
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <div style="flex: 1; font-size: 13px; font-weight: 500;">
                                    ${escapeHtml(cat)}
                                </div>
                                <div style="flex: 2; height: 8px; background: rgba(255, 255, 255, 0.05); border-radius: 4px; overflow: hidden;">
                                    <div style="height: 100%; background: ${catColors.color}; width: ${Number(prob)}%; transition: width 0.3s ease;"></div>
                                </div>
                                <div style="width: 60px; text-align: right; font-size: 13px; font-weight: 700; color: ${catColors.color};">
                                    ${Number(prob).toFixed(1)}%
                                </div>
                            </div>
                        `;
                    }).join("")}
                </div>
            </div>

            ${
                (accuracy != null || Object.keys(modelMetrics).length > 0) ? `
                    <div style="border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 16px; margin-top: 16px;">
                        <h4 style="margin-bottom: 12px; font-size: 14px; color: var(--accent);">Характеристики модели</h4>
                        <div style="display: grid; gap: 8px; font-size: 13px;">
                            ${accuracy != null ? `<div>Точность на тестовой выборке: <b>${Number(accuracy).toFixed(1)}%</b></div>` : ""}
                            ${modelMetrics.f1_macro != null ? `<div>F1-macro: <b>${Number(modelMetrics.f1_macro).toFixed(1)}%</b></div>` : ""}
                            ${modelMetrics.precision_macro != null ? `<div>Precision-macro: <b>${Number(modelMetrics.precision_macro).toFixed(1)}%</b></div>` : ""}
                            ${modelMetrics.precision_weighted != null ? `<div>Precision-weighted: <b>${Number(modelMetrics.precision_weighted).toFixed(1)}%</b></div>` : ""}
                            ${modelMetrics.recall_macro != null ? `<div>Recall-macro: <b>${Number(modelMetrics.recall_macro).toFixed(1)}%</b></div>` : ""}
                            ${modelMetrics.recall_weighted != null ? `<div>Recall-weighted: <b>${Number(modelMetrics.recall_weighted).toFixed(1)}%</b></div>` : ""}
                            ${modelMetrics.f1_weighted != null ? `<div>F1-weighted: <b>${Number(modelMetrics.f1_weighted).toFixed(1)}%</b></div>` : ""}
                            ${modelMetrics.train_size != null ? `<div>Размер обучающей выборки: <b>${modelMetrics.train_size}</b></div>` : ""}
                            ${modelMetrics.test_size != null ? `<div>Размер тестовой выборки: <b>${modelMetrics.test_size}</b></div>` : ""}
                        </div>
                    </div>
                ` : ""
            }

            ${details.interpretation ? `
                <div style="border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 16px; margin-top: 16px;">
                    <h4 style="margin-bottom: 8px; font-size: 14px; color: var(--accent);">Интерпретация</h4>
                    <div style="font-size: 13px; line-height: 1.5; color: var(--text);">
                        ${escapeHtml(details.interpretation)}
                    </div>
                </div>
            ` : ""}

            <div style="margin-top: 16px; font-size: 12px; color: var(--muted); text-align: center;">
                Модель: ${escapeHtml(data.model_name || "RandomForestClassifier")}
            </div>
        </div>
    `;
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
        initSmartTabs();
        loadFilterOptions();
    });
} else {
    initSmartTabs();
    loadFilterOptions();
}