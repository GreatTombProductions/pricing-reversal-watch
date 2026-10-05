"""Parser tests — run against the committed captures (no network)."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "pipeline"))

import parse  # noqa: E402
import pytest  # noqa: E402

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
    # status labels are kept verbatim and never leak into the name
    assert by_name["Claude Mythos 5.1"]["flags"] == ["limited availability"]
    haiku35 = by_name["Claude Haiku 3.5"]
    assert haiku35["retired"] is True
    assert haiku35["flags"] == ["retired, except on Bedrock and Google Cloud"]
    assert not any("(" in m["name"] for m in out["models"])


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


# --- 2026-10 layout: group header row, Name/Input/Output/... labels, taglines,
# status in icon aria-labels, vendor notes in popovers.

OCT = "2026-10-06-platform.claude.com-pricing.html"


def test_anthropic_october_layout_maps_columns_by_label() -> None:
    out = parse.parse_anthropic(_doc(OCT))
    by_name = {m["name"]: m for m in out["models"]}
    assert len(out["models"]) == 19
    assert "Name" not in by_name and "Additional models" not in by_name
    opus55 = by_name["Claude Opus 5.5"]
    # Output is the 3rd column in this layout; positional reading put it under 5m writes
    assert (opus55["input"], opus55["output"]) == (4.0, 20.0)
    assert (opus55["cache_write_5m"], opus55["cache_write_1h"], opus55["cache_hit"]) == (5.0, 8.0, 0.2)
    assert opus55["description"] == "For long-running agentic coding and knowledge work"
    assert by_name["Claude Opus 5"]["output"] == 25.0
    assert by_name["Claude Sonnet 5.5"]["input"] == 2.0


def test_anthropic_october_status_comes_from_popover_wording() -> None:
    by_name = {m["name"]: m for m in parse.parse_anthropic(_doc(OCT))["models"]}
    assert by_name["Claude Opus 4"]["flags"] == ["retired, except on Google Cloud"]
    assert by_name["Claude Opus 4"]["retired"] is True
    assert by_name["Claude Mythos 5.1"]["flags"] == ["Invite only"]
    assert by_name["Claude Mythos 5.1"]["retired"] is False


def test_anthropic_october_cancellation_survives_as_cell_footnote() -> None:
    out = parse.parse_anthropic(_doc(OCT))
    assert not any("will not occur" in c for c in out["callouts"])  # no longer a visible callout
    notes = [n for n in out["cell_notes"] if "will not occur" in n["text"]]
    assert len(notes) == 1
    assert notes[0]["anchor"] == "claude-sonnet-5-introductory-pricing"
    assert "will not occur" in parse.capture_text(_doc(OCT))


def _model_pricing_table(header_cells: list[str], row_cells: list[str]) -> str:
    head = "".join(f"<th>{c}</th>" for c in header_cells)
    row = "".join(f"<td>{c}</td>" for c in row_cells)
    return f"<h2>Model pricing</h2><table><tr>{head}</tr><tr>{row}</tr></table>"


def test_anthropic_fails_closed_when_a_column_label_disappears() -> None:
    doc = _model_pricing_table(
        ["Name", "Input", "Output", "5m writes", "Hits and refreshes"],  # 1h writes missing
        ["Claude X", "$1 / MTok", "$5 / MTok", "$1.25 / MTok", "$0.10 / MTok"],
    )
    with pytest.raises(parse.ParseError):
        parse.parse_anthropic(doc)


def test_anthropic_fails_closed_on_a_priceless_cell() -> None:
    doc = _model_pricing_table(
        ["Name", "Input", "Output", "5m writes", "1h writes", "Hits and refreshes"],
        ["Claude X", "$1 / MTok", "contact sales", "$1.25 / MTok", "$2 / MTok", "$0.10 / MTok"],
    )
    with pytest.raises(parse.ParseError):
        parse.parse_anthropic(doc)


def test_anthropic_reordered_columns_still_map_correctly() -> None:
    doc = _model_pricing_table(
        ["Hits and refreshes", "Output", "Name", "1h writes", "Input", "5m writes"],
        ["$0.10 / MTok", "$5 / MTok", "Claude X", "$2 / MTok", "$1 / MTok", "$1.25 / MTok"],
    )
    (m,) = parse.parse_anthropic(doc)["models"]
    assert (m["name"], m["input"], m["output"], m["cache_hit"]) == ("Claude X", 1.0, 5.0, 0.1)


def test_boundary_page_does_not_read_opus_5_inside_opus_5_5() -> None:
    out = parse.parse_claude_com(_doc("2026-10-06-claude.com-pricing.html"))
    blocks = {(b["name"], b["input"], b["output"]) for b in out["price_blocks"]}
    assert ("Opus 5.5", 4.0, 20.0) in blocks
    assert ("Opus 5", 5.0, 25.0) in blocks
    assert ("Opus 5", 4.0, 20.0) not in blocks
    assert ("Sonnet 5.5", 2.0, 10.0) in blocks


def test_deepseek_october_schedule_keeps_both_sentences() -> None:
    out = parse.parse_deepseek_pricing(_doc("2026-10-06-api-docs.deepseek.com-pricing.html"))
    assert out["schedule_quote"] == (
        "Peak hours are 01:00 - 04:00 and 06:00 - 10:00 UTC, Monday through Friday, excluding "
        "Chinese public holidays. All other hours are off-peak, including weekends and Chinese "
        "public holidays in full."
    )
    foot = {f["n"]: f["text"] for f in out["footnotes"]}
    assert set(foot) == {1, 2, 3}
    assert not any("Deduction Rules" in t or "Copyright" in t for t in foot.values())
    assert not any("continue providing API services" in t for t in foot.values())
