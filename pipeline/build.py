#!/usr/bin/env python3
"""build.py — assemble the Pricing-Reversal Watch dataset.

Flow:
  1. For each source: attempt a live fetch (multi-transport, 60s deadline).
     - success  -> save capture to data/raw/{today}-{slug}.html; receipt = fresh
     - failure  -> fall back to the newest local capture (flagged "stale-capture");
                   a source with no local capture becomes a documented gap.
     A fetch failure is ALWAYS recorded with its transport errors — never silent.
  2. Parse each capture (pure functions from parse.py).
  3. Verify every capture quote in events.py against the captured text —
     build FAILS CLOSED on a quote it cannot find.
  4. Assemble data/generated/index.json.

Run:  python3 pipeline/build.py [--no-fetch]
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import events as events_mod  # noqa: E402
import fetch as fetch_mod  # noqa: E402
import parse as parse_mod  # noqa: E402

PROJECT = Path(__file__).resolve().parents[1]
CAPTURES = PROJECT / "data" / "raw"
OUT = PROJECT / "data" / "generated" / "index.json"
TODAY = date.today().isoformat()

SOURCES = [
    {
        "id": "anthropic-docs",
        "slug": "platform.claude.com-pricing",
        "url": "https://platform.claude.com/docs/en/about-claude/pricing",
        "parser": parse_mod.parse_anthropic,
        "vendor": "anthropic",
        "label": "Anthropic model pricing (docs)",
    },
    {
        "id": "claude-com",
        "slug": "claude.com-pricing",
        "url": "https://claude.com/pricing",
        "parser": parse_mod.parse_claude_com,
        "vendor": "anthropic",
        "label": "Anthropic boundary pricing page",
    },
    {
        "id": "deepseek-pricing",
        "slug": "api-docs.deepseek.com-pricing",
        "url": "https://api-docs.deepseek.com/quick_start/pricing/",
        "parser": parse_mod.parse_deepseek_pricing,
        "vendor": "deepseek",
        "label": "DeepSeek Models & Pricing",
    },
    {
        "id": "deepseek-updates",
        "slug": "api-docs.deepseek.com-updates",
        "url": "https://api-docs.deepseek.com/updates/",
        "parser": parse_mod.parse_deepseek_updates,
        "vendor": "deepseek",
        "label": "DeepSeek API changelog",
    },
    {
        "id": "openai-api-pricing",
        "slug": "openai.com-api-pricing",
        "url": "https://openai.com/api/pricing/",
        "parser": None,  # no parser yet; capture-first until the page is reachable
        "vendor": "openai",
        "label": "OpenAI API pricing",
    },
]


def newest_local_capture(slug: str):
    candidates = sorted(CAPTURES.glob(f"*-{slug}.html"))
    return candidates[-1] if candidates else None


def norm_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def load_capture_index() -> dict:
    """Every committed capture, keyed by file stem and by {source_id}-{date}."""
    index = {}
    for path in sorted(CAPTURES.glob("*.html")):
        m = re.match(r"(\d{4}-\d{2}-\d{2})-(.+)\.html$", path.name)
        if not m:
            continue
        date_str, slug = m.groups()
        doc = path.read_text(encoding="utf-8", errors="replace")
        text = norm_ws(parse_mod.capture_text(doc))
        entry = {"date": date_str, "slug": slug, "text": text, "path": path}
        index[path.stem] = entry
        for src in SOURCES:
            if src["slug"] == slug:
                index[f"{src['id']}-{date_str}"] = entry
    return index


def capture_catalog(index: dict) -> list[dict]:
    """Every committed capture, so evidence from earlier dates keeps its link.

    Receipts describe the latest fetch per source; events also cite older
    captures. Each catalog entry carries the capture id(s), file and SHA-256.
    """
    by_path: dict = {}
    for key, entry in index.items():
        item = by_path.setdefault(
            entry["path"],
            {
                "file": f"data/raw/{entry['path'].name}",
                "date": entry["date"],
                "sha256": fetch_mod.file_sha256(entry["path"]),
                "bytes": entry["path"].stat().st_size,
                "ids": [],
            },
        )
        if key != entry["path"].stem:
            item["ids"].append(key)
    return sorted(by_path.values(), key=lambda c: (c["date"], c["file"]))


def verify_quotes(events: list, index: dict) -> list[str]:
    """Every event capture-quote must be found in the referenced capture text.

    Returns a list of failure descriptions (empty = all verified). The build
    fails closed when this is non-empty: an event whose quote cannot be
    located is treated as fabrication risk, not as a cosmetic error.
    """
    failures = []
    for ev in events:
        for item in ev["evidence"]:
            if item["type"] == "capture" and item.get("quote"):
                cap_id = item["capture"]
                entry = index.get(cap_id)
                if entry is None:
                    failures.append(f"{ev['id']}: capture {cap_id} not available")
                    continue
                if norm_ws(item["quote"]) not in entry["text"]:
                    failures.append(f"{ev['id']}: quote not found in {cap_id}: {item['quote'][:90]}...")
    return failures


def run(do_fetch: bool = True) -> dict:
    receipts = []
    parsed = {}
    capture_texts = {}

    for src in SOURCES:
        receipt = {"id": src["id"], "url": src["url"], "label": src["label"], "vendor": src["vendor"]}
        path = None
        if do_fetch:
            result = fetch_mod.fetch(src["url"], deadline=60.0)
            receipt.update(
                {
                    "fetch_status": result["status"],
                    "http_code": result["http_code"],
                    "transport": result["transport"],
                    "attempted_at": result["captured_at"],
                    "attempts": result["attempts"],
                }
            )
            if result["status"] == "ok":
                path = CAPTURES / f"{TODAY}-{src['slug']}.html"
                saved = fetch_mod.save_capture(result["body"], path)
                receipt["bytes"] = saved["bytes"]
                receipt["sha256"] = saved["sha256"]
                receipt["capture_state"] = "fresh"
                receipt["captured_at"] = result["captured_at"]
            else:
                receipt["error"] = result["error"]
        else:
            receipt.update({"fetch_status": "skipped", "capture_state": None})

        if path is None:
            fallback = newest_local_capture(src["slug"])
            if fallback is not None:
                path = fallback
                receipt["sha256"] = fetch_mod.file_sha256(path)
                receipt["bytes"] = path.stat().st_size
                receipt["captured_at"] = datetime.fromtimestamp(
                    path.stat().st_mtime, tz=timezone.utc
                ).isoformat(timespec="seconds")
                receipt["capture_state"] = receipt.get("capture_state") or "stale-capture"
                if receipt.get("fetch_status") == "ok":
                    receipt["capture_state"] = "fresh"
                elif receipt.get("fetch_status") not in ("ok", "skipped"):
                    receipt["capture_state"] = "stale-capture"
            else:
                receipt["capture_state"] = "none"

        if path is not None:
            receipt["file"] = f"data/raw/{path.name}"
            m = re.match(r"(\d{4}-\d{2}-\d{2})-", path.name)
            receipt["capture_id"] = f"{src['id']}-{m.group(1)}" if m else src["id"]
            doc = path.read_text(encoding="utf-8", errors="replace")
            capture_texts[src["id"]] = norm_ws(parse_mod.capture_text(doc))
            if src["parser"] is not None:
                try:
                    parsed[src["id"]] = src["parser"](doc)
                except parse_mod.ParseError as exc:
                    # Layout drift stops the build: publishing values read from
                    # the wrong column is worse than publishing nothing new.
                    print(f"PARSE FAILED for {src['id']} ({path.name}): {exc}", file=sys.stderr)
                    print("Build fails closed; update the parser against this capture.", file=sys.stderr)
                    raise SystemExit(3)
                receipt["parsed"] = True
            else:
                receipt["parsed"] = False
                receipt["note"] = "captured but not parsed (no parser yet)"
        receipts.append(receipt)

    # -- quote verification (fail closed) -------------------------------------
    capture_index = load_capture_index()
    failures = verify_quotes(events_mod.EVENTS, capture_index)
    if failures:
        print("QUOTE VERIFICATION FAILED (build fails closed):", file=sys.stderr)
        for f in failures:
            print("  -", f, file=sys.stderr)
        raise SystemExit(2)

    # -- assemble vendors ------------------------------------------------------
    anthropic_parse = parsed.get("anthropic-docs", {})
    claude_com_parse = parsed.get("claude-com", {})
    ds_parse = parsed.get("deepseek-pricing", {})
    ds_updates = parsed.get("deepseek-updates", {})

    callouts = anthropic_parse.get("callouts", [])
    cell_notes = anthropic_parse.get("cell_notes", [])

    def _is_featured(text: str) -> bool:
        return "will not occur" in text or "standard price" in text

    featured = [{"text": c, "where": "visible note on the captured pricing page"} for c in callouts if _is_featured(c)]
    featured += [
        {"text": n["text"], "where": "footnote on a price cell of the captured pricing page (shown as a popover)"}
        for n in cell_notes
        if _is_featured(n["text"]) and all(n["text"] != f["text"] for f in featured)
    ]

    vendors = {
        "anthropic": {
            "name": "Anthropic",
            "status": "captured",
            "pricing_url": "https://platform.claude.com/docs/en/about-claude/pricing",
            "boundary_url": "https://claude.com/pricing",
            "captures": [r["id"] for r in receipts if r["vendor"] == "anthropic" and r.get("file")],
            "models": anthropic_parse.get("models", []),
            "callouts_featured": featured,
            "callouts_total": len(callouts),
            "cell_notes": cell_notes,
            "boundary_blocks": claude_com_parse.get("price_blocks", []),
        },
        "deepseek": {
            "name": "DeepSeek",
            "status": "captured",
            "pricing_url": "https://api-docs.deepseek.com/quick_start/pricing/",
            "updates_url": "https://api-docs.deepseek.com/updates/",
            "captures": [r["id"] for r in receipts if r["vendor"] == "deepseek" and r.get("file")],
            "models": ds_parse.get("models", []),
            "schedule_quote": ds_parse.get("schedule_quote"),
            "footnotes": ds_parse.get("footnotes", []),
            "changelog": [
                {"date": e["date"], "title": e["title"], "excerpt": norm_ws(e["text"])[:500]}
                for e in ds_updates.get("entries", [])[:10]
            ],
        },
        "openai": {
            "name": "OpenAI",
            "status": "gap",
            "gap_reason": (
                "Both transports were blocked at the latest capture attempt (HTTP 403). "
                "No vendor page is held; provisional items below are third-party reports, "
                "not vendor-verified."
            ),
        },
        "google": {
            "name": "Google / Vertex",
            "status": "gap",
            "gap_reason": "No capture yet — documented gap, not clean.",
        },
        "mistral": {
            "name": "Mistral",
            "status": "gap",
            "gap_reason": "No capture yet — documented gap, not clean.",
        },
        "kimi": {
            "name": "Kimi / Moonshot",
            "status": "gap",
            "gap_reason": "No capture yet — documented gap, not clean.",
        },
    }

    # openai receipt details for the gap block
    oai = next((r for r in receipts if r["id"] == "openai-api-pricing"), None)
    if oai:
        vendors["openai"]["transport_errors"] = [
            f"{a.get('transport')}: {a.get('error') or 'HTTP ' + str(a.get('http_code'))}" for a in oai.get("attempts", [])
        ]
        vendors["openai"]["attempted_at"] = oai.get("attempted_at")

    def sort_key(ev):
        return max([d for d in (ev.get("effective"), ev.get("observed"), ev.get("announced"), ev.get("confirmed"), "") if d] or [""])

    events_sorted = sorted(events_mod.EVENTS, key=sort_key, reverse=True)

    data = {
        "v": 1,
        "tool": "pricing-reversal-watch",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "captured": TODAY,
        "currency": "USD",
        "unit": "per 1,000,000 tokens (MTok) unless noted",
        "coverage_statement": events_mod.COVERAGE_STATEMENT,
        "receipts": [{k: v for k, v in r.items()} for r in receipts],
        "vendors": vendors,
        "events": events_sorted,
        "family_notes": events_mod.FAMILY_NOTES,
        "provisional": events_mod.PROVISIONAL,
        "captures": capture_catalog(capture_index),
        "quote_verification": {"checked": sum(len([i for i in ev["evidence"] if i["type"] == "capture" and i.get("quote")]) for ev in events_mod.EVENTS), "failures": 0},
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")
    for r in receipts:
        print(f"  {r['id']:22} {r.get('capture_state'):13} {r.get('fetch_status'):10} sha={(r.get('sha256') or '')[:12]}")
    print(f"Events: {len(events_sorted)} | quote checks: {data['quote_verification']['checked']} (0 failures)")
    return data


if __name__ == "__main__":
    run(do_fetch="--no-fetch" not in sys.argv)
