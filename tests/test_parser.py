"""Parser tests — run against the committed captures (no network)."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "pipeline"))

import parse  # noqa: E402

CAP = PROJECT / "data" / "raw"


def _doc(name: str) -> str:
    return (CAP / name).read_text(encoding="utf-8", errors="replace")


def test_anthropic_models_contain_expected_values() -> None:
    out = parse.parse_anthropic(_doc("2026-09-12-platform.claude.com-pricing.html"))
    by_name = {m["name"]: m for m in out["models"]}

    assert len(out["models"]) == 17
    sonnet = by_name["Claude Sonnet 5"]
    assert sonnet["input"] == 2.0 and sonnet["output"] == 10.0
    assert sonnet["cache_hit"] == 0.2 and sonnet["cache_write_5m"] == 2.5
    opus = by_name["Claude Opus 5"]
    assert opus["input"] == 5.0 and opus["output"] == 25.0
    fable = by_name["Claude Fable 5"]
    assert fable["input"] == 10.0 and fable["output"] == 50.0
    # flags
    assert any(m["limited"] for m in out["models"])
    assert any(m["retired_note"] for m in out["models"])


def test_anthropic_callout_carries_the_reversal() -> None:
    out = parse.parse_anthropic(_doc("2026-09-12-platform.claude.com-pricing.html"))
    hits = [c for c in out["callouts"] if "will not occur" in c]
    assert len(hits) == 1
    assert "The previously scheduled increase to $3/$15" in hits[0]


def test_boundary_page_shows_sonnet5_at_standard_price() -> None:
    out = parse.parse_claude_com(_doc("2026-09-12-claude.com-pricing.html"))
    blocks = {(b["name"], b["input"], b["output"]) for b in out["price_blocks"]}
    assert ("Sonnet 5", 2.0, 10.0) in blocks
    assert ("Opus 5", 5.0, 25.0) in blocks
    assert ("Haiku 4.5", 1.0, 5.0) in blocks


def test_deepseek_rates_and_bands() -> None:
    out = parse.parse_deepseek_pricing(_doc("2026-09-12-api-docs.deepseek.com-pricing.html"))
    by_id = {m["id"]: m for m in out["models"]}
    flash = by_id["deepseek-flash"]
    assert flash["version"] == "DeepSeek-V4.1-Flash"
    assert flash["rates"]["off_peak"] == {"cache_hit": 0.003, "cache_miss": 0.15, "output": 0.6}
    assert flash["rates"]["peak"] == {"cache_hit": 0.006, "cache_miss": 0.3, "output": 1.2}
    pro = by_id["deepseek-v4-pro"]
    assert pro["rates"]["off_peak"] == {"cache_hit": 0.022, "cache_miss": 0.66, "output": 1.98}
    assert pro["rates"]["peak"] == {"cache_hit": 0.044, "cache_miss": 1.32, "output": 3.96}
    # peak = 2x off-peak, all components
    for model in out["models"]:
        for comp, off in model["rates"]["off_peak"].items():
            assert abs(model["rates"]["peak"][comp] - 2 * off) < 1e-9


def test_deepseek_schedule_and_footnotes() -> None:
    out = parse.parse_deepseek_pricing(_doc("2026-09-12-api-docs.deepseek.com-pricing.html"))
    assert out["schedule_quote"] == (
        "Peak hours are 01:00 - 04:00 and 06:00 - 10:00 UTC, Monday through Friday "
        "(all other hours are off-peak)."
    )
    foot = {f["n"]: f["text"] for f in out["footnotes"]}
    assert set(foot) == {1, 2, 3, 4}
    assert "continue providing API services for DeepSeek V4 Pro" in foot[2]
    assert "Off-peak rates are half of the peak rates" in foot[3]


def test_deepseek_updates_parse_dated_entries() -> None:
    out = parse.parse_deepseek_updates(_doc("2026-09-12-api-docs.deepseek.com-updates.html"))
    assert len(out["entries"]) >= 20
    first = out["entries"][0]
    assert first["date"] == "2026-09-10"
    assert first["title"] == "DeepSeek-V4.1-Flash Release"
    assert "API prices have been reduced accordingly" in first["text"]
    assert "after September 14, 2026" in first["text"]
