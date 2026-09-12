"""Generated-data contract tests + release contract.

These run against the built data/generated/index.json, manifest.json, and the
frontend files — the artifacts that ship.
"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
DATA = json.loads((PROJECT / "data" / "generated" / "index.json").read_text())
MANIFEST = json.loads((PROJECT / "manifest.json").read_text())


def test_schema_and_coverage_of_receipts() -> None:
    assert DATA["v"] == 1
    assert DATA["tool"] == "pricing-reversal-watch"
    assert DATA["currency"] == "USD"
    by_id = {r["id"]: r for r in DATA["receipts"]}
    assert set(by_id) == {"anthropic-docs", "claude-com", "deepseek-pricing", "deepseek-updates", "openai-api-pricing"}
    for rid in ("anthropic-docs", "claude-com", "deepseek-pricing", "deepseek-updates"):
        assert by_id[rid]["capture_state"] == "fresh"
        assert by_id[rid]["sha256"]
        assert by_id[rid]["capture_id"]
    # the blocked source is recorded, with its transport errors quoted
    assert by_id["openai-api-pricing"]["capture_state"] == "none"
    assert by_id["openai-api-pricing"]["fetch_status"] in ("failed", "http_error")
    assert by_id["openai-api-pricing"]["error"]


def test_gaps_are_documented_never_clean() -> None:
    vendors = DATA["vendors"]
    for vid in ("openai", "google", "mistral", "kimi"):
        assert vendors[vid]["status"] == "gap"
        assert vendors[vid]["gap_reason"]
    assert "documented gaps, never clean" in DATA["coverage_statement"]
    assert vendors["openai"]["transport_errors"]


def test_current_anthropic_values_present() -> None:
    models = {m["name"]: m for m in DATA["vendors"]["anthropic"]["models"]}
    assert models["Claude Sonnet 5"]["input"] == 2.0
    assert models["Claude Sonnet 5"]["output"] == 10.0
    assert models["Claude Opus 5"]["input"] == 5.0
    assert models["Claude Opus 5"]["output"] == 25.0
    assert models["Claude Fable 5"]["input"] == 10.0
    assert models["Claude Fable 5"]["output"] == 50.0


def test_deepseek_second_vendor_parsed() -> None:
    models = {m["id"]: m for m in DATA["vendors"]["deepseek"]["models"]}
    flash = models["deepseek-flash"]
    assert flash["version"] == "DeepSeek-V4.1-Flash"
    assert flash["rates"]["off_peak"] == {"cache_hit": 0.003, "cache_miss": 0.15, "output": 0.6}
    assert DATA["vendors"]["deepseek"]["schedule_quote"]
    assert DATA["vendors"]["deepseek"]["changelog"][0]["date"] == "2026-09-10"


def test_seed_timeline_sonnet5_reversal_has_dual_anchors_and_receipts() -> None:
    events = {e["id"]: e for e in DATA["events"]}
    reversal = events["anthropic-sonnet5-increase-cancelled"]
    assert reversal["kind"] == "scheduled_increase_cancelled"
    assert reversal["status"] == "cancelled"
    caps = [i for i in reversal["evidence"] if i["type"] == "capture"]
    assert len(caps) >= 3  # docs 09-12 + docs 09-06 + boundary page
    assert any(i["capture"] == "claude-com-2026-09-12" for i in caps)
    assert any(i["capture"] == "anthropic-docs-2026-09-06" for i in caps)


def test_events_sorted_and_well_formed() -> None:
    assert len(DATA["events"]) == 5
    for ev in DATA["events"]:
        assert ev["id"] and ev["kind"] and ev["title"] and ev["summary"]
        assert ev["vendor"] in DATA["vendors"]
        assert any(i["type"] == "capture" for i in ev["evidence"])
    assert DATA["quote_verification"]["failures"] == 0
    assert DATA["quote_verification"]["checked"] >= 8


def test_family_notes_and_provisional_are_labeled() -> None:
    assert DATA["family_notes"]
    for note in DATA["provisional"]:
        assert "third-party" in note["source"]


def test_manifest_release_contract() -> None:
    assert MANIFEST["status"] == "released"
    assert MANIFEST["github"] == "https://github.com/GreatTombProductions/pricing-reversal-watch"
    assert MANIFEST["url"] == "https://greattombproductions.github.io/pricing-reversal-watch/"
    assert MANIFEST["released_date"]


def test_static_files_exist_and_fetch_flat_data_path() -> None:
    index = (PROJECT / "frontend" / "index.html").read_text()
    app = (PROJECT / "frontend" / "app.js").read_text()
    assert "style.css" in index
    assert "data/index.json" in app
    assert (PROJECT / "frontend" / "methodology.html").exists()
    assert (PROJECT / "frontend" / "sources.html").exists()
