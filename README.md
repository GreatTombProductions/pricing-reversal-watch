# Pricing-Reversal Watch

A dated, per-provider evidence trail of AI API price and spec changes. Every change carries an as-of date and the vendor's own words — so a rescinded increase, a rename, or a price that went up and came back down is as easy to find as a launch discount.

**Live:** https://greattombproductions.github.io/pricing-reversal-watch/

## What it shows

Change events (with before → after values, dates, and verbatim evidence):

- **Anthropic — Sonnet 5:** launched on temporary introductory pricing ($2/$10 through August 31, 2026, with $3/$15 to follow); the scheduled increase was **cancelled before it took effect** and $2/$10 became the standard price. No announcement date was published — the change was first visible in captures on 2026-08-29.
- **DeepSeek — peak/off-peak escalation:** flat pricing replaced by a weekday peak/off-peak schedule effective 2026-08-16 16:00 UTC; Flash components rose 1.57×–5× after advance notice.
- **DeepSeek — V4.1-Flash:** released 2026-09-10 with **Flash prices reduced** (off-peak cache-miss $0.22 → $0.15; output $0.66 → $0.60; cache-hit $0.007 → $0.003) and the legacy `deepseek-v4-flash` names retired.
- **DeepSeek — V4 Pro:** API services continue past September 14, 2026 (continuation notice; since removed from the pricing page, still in the changelog).
- **Anthropic — Opus 5.5:** a cheaper new generation at $4/$20 (cache hits $0.20) while Opus 4.5 through Opus 5 stay at $5/$25. No launch date is published; first seen 2026-10-04.
- **DeepSeek — schedule change:** the peak-hours footnote now excludes Chinese public holidays (off-peak in full). Rates and windows are unchanged; no changelog entry, no published change date. The before and after wording are both quoted from captures.
- **OpenAI:** documented gap — pricing pages returned HTTP 403 from both transports at the latest attempt; third-party items are listed as provisional, never vendor-verified.

Plus the current declared price tables (Anthropic model table; DeepSeek bands) as captured, with cross-generation notes.

## Evidence model

- **Captures** — each monitored page is fetched at build time, saved raw in `data/raw/`, and pinned by a SHA-256 receipt (`data/generated/index.json` → `receipts`). Raw captures are published with the site; every quote can be re-checked.
- **Quote verification** — every event quote is checked against the captured page text at build time; the build fails closed on a quote it cannot locate. Vendor notes a page renders only as popovers (price-cell footnotes, model status notes) count as page text, and the evidence label says where the wording appears.
- **Layout drift fails closed** — the Anthropic table is read by column label, never by position. If an expected label is missing, or a price cell has no price, the build stops instead of publishing values from the wrong column.
- **Monitoring notes** — dated observations recorded while tracking the pages; labeled as notes, never presented as vendor quotes.
- **Gaps are documented** — a failed fetch is recorded with its transport errors; a vendor without a capture is listed as a gap, never as clean.

## Layout

```
pipeline/   fetch.py (multi-transport + deadlines + receipts), parse.py (pure parsers),
            events.py (curated change events), build.py (assemble + verify)
data/raw/   raw vendor HTML captures, date-stamped, SHA-256 pinned
data/       generated/index.json (the dataset the site loads)
frontend/   index.html, methodology.html, sources.html, app.js, style.css
tests/      parser tests, evidence-rule tests, generated-data contract, browser smoke
```

## Rebuild

```bash
python3 pipeline/build.py          # fetch (with fallback to existing captures), verify, assemble
python3 -m pytest -q               # pipeline + contract tests
python3 tests/run_browser_smoke.py # staged static-site smoke (Playwright)
```

## Honesty & scope

Declared values, not verified ones. No advice, no vendor recommendations, no invoice reconciliation, no prediction. "No reversal found" is only claimable over the capture interval. Static site, no backend, no accounts, no tracking.

## License

MIT
