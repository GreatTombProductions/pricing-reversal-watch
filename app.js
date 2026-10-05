/* Pricing-Reversal Watch — frontend rendering. No dependencies. */
"use strict";

const KIND_LABELS = {
  scheduled_increase_cancelled: { label: "increase cancelled", cls: "cancel" },
  price_cut: { label: "price cut", cls: "cut" },
  scheduled_increase_executed: { label: "increase executed", cls: "up" },
  continuation_notice: { label: "continuation notice", cls: "notice" },
  intro_pricing: { label: "intro pricing", cls: "intro" },
  new_generation_cut: { label: "cheaper new generation", cls: "cut" },
  schedule_change: { label: "schedule change", cls: "notice" },
};

const STATUS_LABELS = {
  cancelled: "cancelled",
  executed: "executed",
  active: "active",
  resolved: "resolved",
};

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "text") node.textContent = v;
    else if (k === "html") node.innerHTML = v; // only for static template strings, never vendor text
    else if (k === "class") node.className = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  for (const child of [].concat(children)) {
    if (child == null) continue;
    node.append(typeof child === "string" ? document.createTextNode(child) : child);
  }
  return node;
}

function money(x) {
  if (x == null) return "—";
  return "$" + (Number.isInteger(x) ? x : x.toFixed(x < 1 ? 3 : 2)).toString();
}

function shortSha(sha) {
  return sha ? sha.slice(0, 12) + "…" : "";
}

function captureLink(receipt) {
  if (!receipt || !receipt.file) return null;
  return el("a", {
    href: receipt.file,
    title: "raw capture, sha256 " + (receipt.sha256 || ""),
    text: "capture " + (receipt.captured_at || "").slice(0, 10) + " · " + shortSha(receipt.sha256),
  });
}

/* ---------------------------------------------------------------- timeline */

function evidenceNode(item, receiptsById) {
  if (item.type === "capture") {
    const receipt = receiptsById[item.capture];
    const parts = [
      el("blockquote", { class: "quote", text: "“" + item.quote + "”" }),
      el("p", { class: "evidence-meta" }, [
        item.label ? item.label + " — " : "",
        item.capture,
        receipt ? " · " : "",
        receipt ? captureLink(receipt) : null,
      ]),
    ];
    return el("div", { class: "evidence" }, parts);
  }
  if (item.type === "tracking_note") {
    return el("div", { class: "evidence tracking" }, [
      el("p", { class: "evidence-meta", text: "Monitoring note · " + item.date }),
      el("p", { class: "tracking-text", text: item.text }),
    ]);
  }
  if (item.type === "values") {
    return el("div", { class: "evidence tracking" }, [
      el("p", { class: "evidence-meta", text: "Parsed values · " + item.capture }),
      el("p", { class: "tracking-text", text: item.text }),
    ]);
  }
  return null;
}

function eventCard(ev, receiptsById) {
  const kind = KIND_LABELS[ev.kind] || { label: ev.kind, cls: "notice" };
  const dates = [
    ev.announced ? "announced " + ev.announced : null,
    ev.observed ? "observed " + ev.observed : null,
    ev.confirmed ? "confirmed " + ev.confirmed : null,
    ev.effective ? "effective " + ev.effective : null,
  ].filter(Boolean);

  return el("article", { class: "card event" }, [
    el("div", { class: "event-head" }, [
      el("span", { class: "kind " + kind.cls, text: kind.label }),
      el("span", { class: "status " + ev.status, text: STATUS_LABELS[ev.status] || ev.status }),
      el("span", { class: "event-vendor", text: ev.vendor }),
    ]),
    el("h3", { text: ev.title }),
    el("p", { class: "event-dates", text: dates.join(" · ") }),
    el("div", { class: "values" }, [
      el("div", { class: "val old" }, [el("span", { text: "before" }), el("strong", { text: ev.old_value || "—" })]),
      el("div", { class: "arrow", text: "→" }),
      el("div", { class: "val new" }, [el("span", { text: "after" }), el("strong", { text: ev.new_value || "—" })]),
    ]),
    el("p", { class: "event-summary", text: ev.summary }),
    ...ev.evidence.map((i) => evidenceNode(i, receiptsById)).filter(Boolean),
    ...(ev.notes || []).map((n) => el("p", { class: "event-note", text: n })),
  ]);
}

/* ----------------------------------------------------------------- vendors */

function renderAnthropic(v, receiptsById) {
  const modelsTable = document.getElementById("anthropic-models");
  const head = el("tr", {}, [
    el("th", { text: "Model" }),
    el("th", { text: "Input" }),
    el("th", { text: "Output" }),
    el("th", { text: "Cache hit" }),
    el("th", { text: "Notes" }),
  ]);
  modelsTable.append(head);
  for (const m of v.models) {
    const flags = m.flags || [];
    modelsTable.append(
      el("tr", { class: m.retired ? "retired" : "" }, [
        el("td", { text: m.name }),
        el("td", { class: "num", text: money(m.input) }),
        el("td", { class: "num", text: money(m.output) }),
        el("td", { class: "num", text: money(m.cache_hit) }),
        el("td", { class: "flag", text: flags.join("; ") || "—" }),
      ])
    );
  }

  const calloutHost = document.getElementById("anthropic-callout");
  for (const c of v.callouts_featured) {
    calloutHost.append(
      el("div", { class: "featured-callout" }, [
        el("p", { class: "quote", text: "“" + c.text + "”" }),
        el("p", { class: "evidence-meta", text: "vendor wording — " + c.where }),
      ])
    );
  }

  const boundary = document.getElementById("anthropic-boundary");
  for (const b of v.boundary_blocks) {
    boundary.append(el("li", {}, [
      el("strong", { text: b.name + " " }),
      el("span", { text: money(b.input) + " in / " + money(b.output) + " out per MTok" }),
    ]));
  }
}

function renderDeepseek(v) {
  const modelsTable = document.getElementById("deepseek-models");
  modelsTable.append(
    el("tr", {}, [
      el("th", { text: "Model" }),
      el("th", { text: "Version" }),
      el("th", { text: "Band" }),
      el("th", { text: "Cache hit" }),
      el("th", { text: "Cache miss" }),
      el("th", { text: "Output" }),
    ])
  );
  for (const m of v.models) {
    for (const [band, label] of [["off_peak", "off-peak"], ["peak", "peak"]]) {
      const r = m.rates[band] || {};
      modelsTable.append(
        el("tr", { class: band }, [
          el("td", { text: m.id }),
          el("td", { text: m.version || "—" }),
          el("td", { text: label }),
          el("td", { class: "num", text: money(r.cache_hit) }),
          el("td", { class: "num", text: money(r.cache_miss) }),
          el("td", { class: "num", text: money(r.output) }),
        ])
      );
    }
  }
  document.getElementById("deepseek-schedule").textContent = "“" + (v.schedule_quote || "") + "” — vendor footnote";

  const log = document.getElementById("deepseek-changelog");
  for (const entry of v.changelog.slice(0, 6)) {
    log.append(el("li", {}, [
      el("p", { class: "log-head" }, [el("strong", { text: entry.date + " · " + entry.title })]),
      el("p", { class: "log-body", text: entry.excerpt + (entry.excerpt.length >= 500 ? "…" : "") }),
    ]));
  }
}

/* ----------------------------------------------------------------- sources */

function renderSources(data) {
  const host = document.getElementById("sources-table");
  if (!host) return;
  const table = el("table");
  table.append(
    el("tr", {}, [
      el("th", { text: "Source" }),
      el("th", { text: "URL" }),
      el("th", { text: "Fetch" }),
      el("th", { text: "Captured" }),
      el("th", { text: "SHA-256" }),
      el("th", { text: "Raw" }),
    ])
  );
  for (const r of data.receipts) {
    const state = r.capture_state === "fresh" ? "captured" : r.capture_state === "stale-capture" ? "stale capture" : "unreachable";
    table.append(
      el("tr", { class: r.capture_state === "none" ? "retired" : "" }, [
        el("td", { text: r.label }),
        el("td", {}, [el("a", { href: r.url, text: r.url, rel: "noopener" })]),
        el("td", { text: state + (r.http_code ? " (HTTP " + r.http_code + ")" : "") }),
        el("td", { text: (r.captured_at || "").slice(0, 10) }),
        el("td", { class: "mono", title: r.sha256 || "", text: r.sha256 ? shortSha(r.sha256) : "—" }),
        el("td", {}, r.file ? [el("a", { href: r.file, text: "html" })] : [document.createTextNode("—")]),
      ])
    );
  }
  host.append(table);
  const summary = document.getElementById("sources-summary");
  if (summary) {
    summary.textContent =
      data.quote_verification.checked +
      " event quotes were verified against these captures at build time (" +
      data.quote_verification.failures +
      " failures — the build fails closed on an unverifiable quote).";
  }
  const coverage = document.getElementById("sources-coverage");
  if (coverage) coverage.textContent = data.coverage_statement;
}

/* -------------------------------------------------------------------- main */

async function main() {
  let data;
  try {
    const response = await fetch("data/index.json", { cache: "no-store" });
    data = await response.json();
  } catch (err) {
    document.body.prepend(el("p", { class: "load-error", text: "Could not load data/index.json: " + err }));
    return;
  }

  // Every committed capture is linkable (older evidence included); the latest
  // fetch receipts overlay their own entries with full timestamps.
  const receiptsById = {};
  for (const c of data.captures || []) {
    for (const id of c.ids) receiptsById[id] = { file: c.file, sha256: c.sha256, captured_at: c.date };
  }
  for (const r of data.receipts) if (r.capture_id) receiptsById[r.capture_id] = r;

  if (document.body.dataset.page === "sources") {
    renderSources(data);
    return;
  }

  document.getElementById("captured-date").textContent = data.captured;
  document.getElementById("event-count").textContent = data.events.length;
  document.getElementById("vendor-count").textContent =
    Object.values(data.vendors).filter((v) => v.status === "captured").length;
  document.getElementById("quote-count").textContent = data.quote_verification.checked;
  document.getElementById("coverage-statement").textContent = data.coverage_statement;

  const timeline = document.getElementById("timeline");
  for (const ev of data.events) timeline.append(eventCard(ev, receiptsById));

  const anthropic = data.vendors.anthropic;
  renderAnthropic(anthropic, receiptsById);
  document.getElementById("anthropic-links").textContent =
    "Captured from " + anthropic.pricing_url + " and " + anthropic.boundary_url + ".";
  for (const n of data.family_notes.filter((x) => x.vendor === "anthropic")) {
    document.getElementById("anthropic-notes").append(el("li", { text: n.text }));
  }

  renderDeepseek(data.vendors.deepseek);
  document.getElementById("deepseek-links").textContent =
    "Captured from " + data.vendors.deepseek.pricing_url + " and " + data.vendors.deepseek.updates_url + ".";
  for (const n of data.family_notes.filter((x) => x.vendor === "deepseek")) {
    document.getElementById("deepseek-notes").append(el("li", { text: n.text }));
  }

  const openai = data.vendors.openai;
  document.getElementById("openai-gap-reason").textContent = openai.gap_reason;
  for (const e of openai.transport_errors || []) {
    document.getElementById("openai-errors").append(el("li", { text: e }));
  }
  for (const p of data.provisional.filter((x) => x.vendor === "openai")) {
    document.getElementById("openai-provisional").append(
      el("li", {}, [
        el("strong", { text: p.date + " — " }),
        el("span", { text: p.text + " " }),
        el("em", { text: "(" + p.source + ")" }),
      ])
    );
  }

  for (const vid of ["google", "mistral", "kimi"]) {
    const v = data.vendors[vid];
    document.getElementById("other-gaps").append(
      el("li", {}, [el("strong", { text: v.name + " — " }), el("span", { text: v.gap_reason })])
    );
  }
}

main();
