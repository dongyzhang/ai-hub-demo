"use strict";

const state = { assets: [], filtered: [], stats: null };

// ---------- boot ----------
document.addEventListener("DOMContentLoaded", init);

async function init() {
  wireTabs();
  wireFilters();
  wireModal();
  try {
    const [assetsDoc, statsDoc] = await Promise.all([
      fetchJSON("data/assets.json"),
      fetchJSON("data/stats.json"),
    ]);
    state.assets = assetsDoc.assets || [];
    state.stats = statsDoc;
    document.getElementById("footer-meta").textContent =
      `${state.assets.length} assets · indexed ${assetsDoc.generated_at || "?"}`;
  } catch (err) {
    document.getElementById("asset-grid").innerHTML =
      `<p>Could not load catalog data. Run <code>python scripts/build_index.py</code> first, ` +
      `then serve with <code>python serve.py</code>.<br><small>${err}</small></p>`;
    return;
  }
  populateFilters();
  applyFilters();
  renderProducts();
  renderTraining();
  renderAnalytics();
  loadReport();
}

function fetchJSON(url) {
  return fetch(url).then((r) => {
    if (!r.ok) throw new Error(`${url}: ${r.status}`);
    return r.json();
  });
}

// ---------- tabs ----------
function wireTabs() {
  document.getElementById("tabs").addEventListener("click", (e) => {
    const btn = e.target.closest(".tab");
    if (!btn) return;
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    btn.classList.add("active");
    const view = btn.dataset.view;
    document.querySelectorAll(".view").forEach((v) => v.classList.add("hidden"));
    document.getElementById(`view-${view}`).classList.remove("hidden");
  });
}

// ---------- filters ----------
function wireFilters() {
  ["search", "filter-category", "filter-type", "filter-team"].forEach((id) =>
    document.getElementById(id).addEventListener("input", applyFilters)
  );
  document.getElementById("clear-filters").addEventListener("click", () => {
    ["search", "filter-category", "filter-type", "filter-team"].forEach(
      (id) => (document.getElementById(id).value = "")
    );
    applyFilters();
  });
}

function populateFilters() {
  fillSelect("filter-category", uniq(state.assets.map((a) => a.category)));
  fillSelect("filter-type", uniq(state.assets.map((a) => a.type)));
  fillSelect("filter-team", uniq(state.assets.map((a) => a.team)));
}

function fillSelect(id, values) {
  const sel = document.getElementById(id);
  values.sort().forEach((v) => {
    const o = document.createElement("option");
    o.value = v;
    o.textContent = v;
    sel.appendChild(o);
  });
}

function applyFilters() {
  const q = document.getElementById("search").value.toLowerCase().trim();
  const cat = document.getElementById("filter-category").value;
  const type = document.getElementById("filter-type").value;
  const team = document.getElementById("filter-team").value;

  state.filtered = state.assets.filter((a) => {
    if (cat && a.category !== cat) return false;
    if (type && a.type !== type) return false;
    if (team && a.team !== team) return false;
    if (q) {
      const hay = [
        a.title, a.description, a.category, a.type, a.team, a.author,
        (a.tags || []).join(" "), (a.tools || []).join(" "),
      ].join(" ").toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });

  document.getElementById("result-count").textContent =
    `${state.filtered.length} of ${state.assets.length} assets`;
  renderGrid("asset-grid", state.filtered);
}

// ---------- rendering ----------
function renderGrid(targetId, assets) {
  const grid = document.getElementById(targetId);
  if (!assets.length) {
    grid.innerHTML = `<p class="result-count">No matching assets.</p>`;
    return;
  }
  grid.innerHTML = "";
  assets.forEach((a) => grid.appendChild(card(a)));
}

function card(a) {
  const el = document.createElement("div");
  el.className = "card";
  el.innerHTML = `
    <div class="card-top">
      <h3>${esc(a.title)}</h3>
      <span class="badge">${esc(a.type)}</span>
    </div>
    <p>${esc(a.description)}</p>
    <div class="card-meta">
      <span class="chip cat">${esc(a.category)}</span>
      <span class="chip">${esc(a.team)}</span>
      ${(a.tags || []).slice(0, 3).map((t) => `<span class="chip">#${esc(t)}</span>`).join("")}
    </div>`;
  el.addEventListener("click", () => openDetail(a));
  return el;
}

function renderProducts() {
  const products = state.assets.filter((a) => a.type === "app");
  renderGrid("product-grid", products);
}

function renderTraining() {
  const training = state.assets.filter((a) => a.type === "training");
  const list = document.getElementById("training-list");
  if (!training.length) {
    list.innerHTML = `<p class="result-count">No training content yet.</p>`;
    return;
  }
  list.innerHTML = "";
  training.forEach((a) => {
    const el = document.createElement("div");
    el.className = "card";
    el.innerHTML = `
      <div>
        <h3>${esc(a.title)}</h3>
        <p>${esc(a.description)}</p>
      </div>
      <span class="badge">${esc(a.team)}</span>`;
    el.addEventListener("click", () => openDetail(a));
    list.appendChild(el);
  });
}

// ---------- analytics ----------
function renderAnalytics() {
  const s = state.stats;
  if (!s) return;
  const cards = [
    ["Total assets", s.total],
    ["Categories", (s.by_category || []).length],
    ["Teams", (s.by_team || []).length],
    ["Contributors", (s.top_contributors || []).length],
  ];
  document.getElementById("stat-cards").innerHTML = cards
    .map(([lbl, num]) => `<div class="stat-card"><div class="num">${num}</div><div class="lbl">${lbl}</div></div>`)
    .join("");

  barChart("chart-category", s.by_category);
  barChart("chart-type", s.by_type);
  barChart("chart-team", s.by_team);
  barChart("chart-month", s.by_month);
  rankList("contributors", s.top_contributors);
  rankList("tools", s.top_tools);
}

function barChart(id, data) {
  const el = document.getElementById(id);
  if (!data || !data.length) { el.innerHTML = "<p class='lbl'>No data.</p>"; return; }
  const max = Math.max(...data.map((d) => d.count));
  el.innerHTML = data
    .map((d) => {
      const pct = Math.round((d.count / max) * 100);
      return `<div class="bar-row">
        <span class="name" title="${esc(d.name)}">${esc(d.name)}</span>
        <span class="bar-track"><span class="bar-fill" style="width:${pct}%"></span></span>
        <span class="val">${d.count}</span>
      </div>`;
    })
    .join("");
}

function rankList(id, data) {
  const el = document.getElementById(id);
  if (!data || !data.length) { el.innerHTML = "<p class='lbl'>No data.</p>"; return; }
  el.innerHTML = data
    .map((d) => `<div class="rank"><span>${esc(d.name)}</span><span>${d.count}</span></div>`)
    .join("");
}

async function loadReport() {
  const el = document.getElementById("report");
  try {
    const res = await fetch("data/report.md");
    if (!res.ok) throw new Error(res.status);
    el.innerHTML = renderMarkdown(await res.text());
  } catch (e) {
    el.innerHTML = `<p class="lbl">No report yet. Run <code>python scripts/generate_report.py</code>.</p>`;
  }
}

// ---------- detail modal ----------
function wireModal() {
  document.getElementById("modal-close").addEventListener("click", closeDetail);
  document.getElementById("overlay").addEventListener("click", (e) => {
    if (e.target.id === "overlay") closeDetail();
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeDetail(); });
}

function openDetail(a) {
  const meta = [
    ["Type", a.type], ["Category", a.category], ["Team", a.team],
    ["Author", a.author], ["Created", a.created],
  ];
  const tags = (a.tags || []).map((t) => `<span class="chip">#${esc(t)}</span>`).join("");
  const tools = (a.tools || []).map((t) => `<span class="chip">${esc(t)}</span>`).join("");
  const demo = a.demo_url ? `<p><a href="${esc(a.demo_url)}" target="_blank" rel="noopener">Open demo ↗</a></p>` : "";
  document.getElementById("modal-body").innerHTML = `
    <h1>${esc(a.title)}</h1>
    <p style="color:var(--ink-soft)">${esc(a.description)}</p>
    <div class="modal-meta">
      ${meta.map(([k, v]) => `<span class="chip"><b>${k}:</b> ${esc(v || "—")}</span>`).join("")}
    </div>
    <div class="modal-meta">${tags} ${tools}</div>
    ${demo}
    <p class="lbl">Repo path: <code>${esc(a.path || "")}</code></p>
    <hr/>
    <div class="markdown">${renderMarkdown(a.readme || "_No README provided._")}</div>`;
  document.getElementById("overlay").classList.remove("hidden");
}

function closeDetail() {
  document.getElementById("overlay").classList.add("hidden");
}

// ---------- helpers ----------
function uniq(arr) { return [...new Set(arr.filter(Boolean))]; }

function esc(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// Minimal, safe Markdown renderer (escapes first, then applies inline/block rules).
function renderMarkdown(md) {
  const lines = md.replace(/\r\n/g, "\n").split("\n");
  let html = "";
  let inUl = false, inOl = false, inCode = false;
  const closeLists = () => {
    if (inUl) { html += "</ul>"; inUl = false; }
    if (inOl) { html += "</ol>"; inOl = false; }
  };
  for (const raw of lines) {
    if (raw.trim().startsWith("```")) {
      if (inCode) { html += "</code></pre>"; inCode = false; }
      else { closeLists(); html += "<pre><code>"; inCode = true; }
      continue;
    }
    if (inCode) { html += esc(raw) + "\n"; continue; }

    const line = raw.trimEnd();
    if (!line.trim()) { closeLists(); continue; }

    const h = line.match(/^(#{1,6})\s+(.*)$/);
    if (h) { closeLists(); html += `<h${h[1].length}>${inline(h[2])}</h${h[1].length}>`; continue; }
    if (/^(-{3,}|\*{3,})$/.test(line.trim())) { closeLists(); html += "<hr/>"; continue; }

    const ul = line.match(/^\s*[-*]\s+(.*)$/);
    if (ul) { if (!inUl) { closeLists(); html += "<ul>"; inUl = true; } html += `<li>${inline(ul[1])}</li>`; continue; }

    const ol = line.match(/^\s*\d+\.\s+(.*)$/);
    if (ol) { if (!inOl) { closeLists(); html += "<ol>"; inOl = true; } html += `<li>${inline(ol[1])}</li>`; continue; }

    closeLists();
    html += `<p>${inline(line)}</p>`;
  }
  if (inCode) html += "</code></pre>";
  closeLists();
  return html;
}

function inline(text) {
  let t = esc(text);
  t = t.replace(/`([^`]+)`/g, "<code>$1</code>");
  t = t.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  t = t.replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>");
  t = t.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  return t;
}
