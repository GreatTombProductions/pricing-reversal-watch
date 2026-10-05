# Pricing-Reversal Watch — Project Spec

**Status:** built and released 2026-09-12; refreshed 2026-10-06 (captures re-pinned, label-mapped Anthropic parser that fails closed, popover-note extraction, capture catalog, two new events).
**Sibling family:** Model Lifecycle Watch, Notice-Policy Check, Model Release Status Verifier, API Rate-Window Clock.

## The tool, in one sentence

A static per-provider evidence trail of AI API price and spec changes — each change carries an as-of date and verbatim evidence — so a developer can see "price cut in August, reversed in September" (or "scheduled increase cancelled") at a glance instead of re-reading changelogs.

## Decision boundary & asymmetry

AI-API customers (developers, small teams with products on a model family) at the purchase / migration / stay decision boundary. Vendors profit from asymmetric announcement: promotional cuts get press and migration pull; reversals, scheduled-increase cancellations, renames, and spec changes arrive as a changelog line or not at all — locking migrated workloads into terms they didn't see coming. A neutral evidence trail makes "the increase was cancelled" as legible as "the price went down."

## Evidence rules (load-bearing)

1. Fetch failure = flagged finding, never silent (transport errors recorded and displayed).
2. Per-source hard wall-clock deadline (thread + join); multi-transport (urllib → curl fallback); one transport's failure is never "the page moved."
3. Volatile metadata stripped before hashing; canonical JSON hashing for semantic pins.
4. Quote verification at build time — fail closed on an unverifiable quote.
5. Current and historical bases are separate collections; never price a past date from a current page.
6. Absent evidence ≠ no change — uncaptured vendors are documented gaps, never clean.
7. "No reversal found" is claimable only over the capture interval, stated as such.

## Schema (v1)

`data/generated/index.json`: `receipts[]` (id, url, fetch status, transport, sha256, capture file) · `vendors{}` (anthropic: model rows + featured callouts + boundary blocks; deepseek: rate bands + schedule + changelog; openai/google/mistral/kimi: documented gaps) · `events[]` (kind, dates, old→new values, evidence[]) · `family_notes[]` · `provisional[]` · `quote_verification`.

## Frontend

Static, `data/index.json` fetched client-side; per-vendor sections + a change-event timeline; every displayed number links to its capture receipt; methodology + sources pages; raw captures published for auditing; mobile-friendly; `.nojekyll` + LICENSE in deploy.

## Acceptance

1. Seed timeline renders the Sonnet 5 reversal with ≥2 capture anchors + receipts. ✅ (4 anchors: docs 09-12, docs 09-06, boundary page; 10 quotes verified)
2. Current Anthropic prices parsed from live capture (Sonnet 5 $2/$10, Opus 5 $5/$25, Fable 5 $10/$50). ✅
3. Second vendor surface parsed (DeepSeek pricing + changelog) — third (OpenAI) explicitly gap-listed. ✅
4. ≥1 test per evidence rule (deadline, transport fallback, canonical hashing, quote verification). ✅
5. Static release passes browser smoke; manifest complete; hub shows it. ✅
6. Honest-coverage lines for uncaptured vendors/surfaces. ✅

## NOT building

Invoice reconciliation (actuals vs declared), price prediction, rate-limit monitoring beyond snapshot evidence, recommendation/advice surfaces, anything requiring accounts, scheduled re-fetch automation beyond the rebuild pipeline.
