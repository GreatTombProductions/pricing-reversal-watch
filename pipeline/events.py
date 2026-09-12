#!/usr/bin/env python3
"""events.py — curated change events for the seed timeline.

Each event is an interpretation layer over raw captures: it names a change,
its dates, the old -> new values, and evidence. Every `capture` quote is
VERIFIED against the committed capture at build time (build.py fails closed
on a quote it cannot find). Tracking notes are this watch's own dated
observations, recorded while monitoring the vendor pages; they are labeled
as notes, not vendor quotes.
"""

EVENTS = [
    {
        "id": "anthropic-sonnet5-intro",
        "vendor": "anthropic",
        "family": "Claude Sonnet 5",
        "kind": "intro_pricing",
        "title": "Sonnet 5 launches on temporary introductory pricing",
        "summary": (
            "Sonnet 5 launched with $2/$10 per MTok labeled as introductory pricing through "
            "August 31, 2026, with a standard price of $3/$15 to follow. The temporary label is "
            "the setup for the reversal below: the increase was scheduled, announced, and then "
            "cancelled before it took effect."
        ),
        "announced": "2026-06-30",
        "observed": "2026-07-19",
        "effective": "2026-06-30",
        "status": "resolved",
        "old_value": None,
        "new_value": "$2 / $10 per MTok introductory through 2026-08-31; $3 / $15 standard to follow",
        "evidence": [
            {
                "type": "capture",
                "capture": "anthropic-docs-2026-09-12",
                "quote": "announced at launch as introductory pricing through August 31, 2026",
            },
            {
                "type": "tracking_note",
                "date": "2026-07-19",
                "text": (
                    "Monitoring note: Sonnet 5 recorded as released June 30 at $2/$10 introductory "
                    "pricing through August 31; standard pricing $3/$15 listed to follow."
                ),
            },
        ],
        "notes": [],
    },
    {
        "id": "anthropic-sonnet5-increase-cancelled",
        "vendor": "anthropic",
        "family": "Claude Sonnet 5",
        "kind": "scheduled_increase_cancelled",
        "title": "Scheduled increase cancelled — $2/$10 becomes the standard price",
        "summary": (
            "The previously scheduled increase to $3/$15 on September 1, 2026 did not occur. "
            "$2/$10 is now the standard price. No announcement date for the cancellation is "
            "published on the pages held here; the change was first visible in captures on "
            "2026-08-29 and confirmed on 2026-08-31. Monitoring as of 2026-08-21 still listed "
            "the increase as scheduled — the reversal appeared quietly."
        ),
        "announced": None,
        "observed": "2026-08-29",
        "confirmed": "2026-08-31",
        "effective": None,
        "status": "cancelled",
        "old_value": "$3 / $15 scheduled for 2026-09-01",
        "new_value": "increase will not occur — $2 / $10 is the standard price",
        "evidence": [
            {
                "type": "capture",
                "capture": "anthropic-docs-2026-09-12",
                "quote": (
                    "The $2/$10 per million input/output token pricing for Claude Sonnet 5, "
                    "announced at launch as introductory pricing through August 31, 2026, is now "
                    "the standard price. The previously scheduled increase to $3/$15 per million "
                    "input/output tokens on September 1, 2026 will not occur."
                ),
            },
            {
                "type": "capture",
                "capture": "anthropic-docs-2026-09-06",
                "quote": (
                    "The previously scheduled increase to $3/$15 per million input/output tokens "
                    "on September 1, 2026 will not occur"
                ),
                "label": "earlier capture (2026-09-06), same text",
            },
            {
                "type": "capture",
                "capture": "claude-com-2026-09-12",
                "quote": (
                    "Sonnet 5 High-performance model for coding and agents Input $2 / MTok "
                    "Output $10 / MTok Prompt caching Read $0.20 / MTok Write $2.50 / MTok"
                ),
                "label": "boundary page — $2/$10, no introductory label",
            },
            {
                "type": "tracking_note",
                "date": "2026-08-31",
                "text": (
                    "Monitoring note: dual anchor confirmed (pricing docs callout + boundary page). "
                    "Through 2026-08-21 the increase was still listed as scheduled; page change first "
                    "noticed 2026-08-29."
                ),
            },
        ],
        "notes": [
            "The cancellation is the exact shape this watch exists for: a scheduled, announced "
            "increase that was quietly rescinded, visible only to someone re-reading the pricing page.",
        ],
    },
    {
        "id": "deepseek-peak-offpeak-executed",
        "vendor": "deepseek",
        "family": "deepseek-flash / deepseek-v4-pro",
        "kind": "scheduled_increase_executed",
        "title": "Peak/off-peak billing goes live — Flash components up 1.57×–5×",
        "summary": (
            "DeepSeek replaced flat token pricing with a peak/off-peak schedule effective "
            "2026-08-16 16:00 UTC. The notice was published in advance and the schedule took "
            "effect on time. This is the executed-increase case that the cancellation above "
            "contrasts with — and it is the basis the September cut (below) moves down from."
        ),
        "announced": "2026-08-15",
        "observed": "2026-08-15",
        "effective": "2026-08-16T16:00:00Z",
        "status": "executed",
        "old_value": (
            "flat pricing — flash $0.0028 / $0.14 / $0.28; pro $0.003625 / $0.435 / $0.87 "
            "(cache-hit / cache-miss / output, per MTok)"
        ),
        "new_value": (
            "off-peak — flash $0.007 / $0.22 / $0.66; pro $0.022 / $0.66 / $1.98 "
            "(peak = 2×); new weekday peak windows 01:00–04:00 and 06:00–10:00 UTC"
        ),
        "evidence": [
            {
                "type": "capture",
                "capture": "deepseek-pricing-2026-09-12",
                "quote": (
                    "Off-peak rates are half of the peak rates. Peak hours are 01:00 - 04:00 "
                    "and 06:00 - 10:00 UTC, Monday through Friday (all other hours are off-peak)."
                ),
                "label": "current schedule (still in effect at capture date)",
            },
            {
                "type": "tracking_note",
                "date": "2026-08-15",
                "text": (
                    "Monitoring note: formal notice recorded — flat pricing replaced by "
                    "peak/off-peak billing effective 2026-08-16 16:00 UTC; Flash components "
                    "increased 1.57×–5× versus the flat basis."
                ),
            },
            {
                "type": "tracking_note",
                "date": "2026-08-28",
                "text": (
                    "Archived rate snapshot: off-peak/peak rates with weekday windows, "
                    "effective-dated; the vendor transition notice read \"The new prices take "
                    "effect at 16:00 UTC on August 16, 2026.\""
                ),
            },
        ],
        "notes": [
            "Advance notice given; schedule executed on time. Components above 2× met a materiality "
            "threshold that monitoring had flagged in advance.",
        ],
    },
    {
        "id": "deepseek-v41-flash-cut",
        "vendor": "deepseek",
        "family": "deepseek-flash",
        "kind": "price_cut",
        "title": "DeepSeek-V4.1-Flash released — Flash prices reduced, legacy names retired",
        "summary": (
            "DeepSeek-V4.1-Flash released and Flash API prices were reduced: off-peak cache-hit "
            "$0.007 → $0.003 (−57%), cache-miss $0.22 → $0.15 (−32%), output $0.66 → $0.60 (−9%). "
            "The legacy model names deepseek-v4-flash and deepseek-v4-flash-vision-exp were "
            "retired and are temporarily routed to the new model. Pro rates were unchanged in "
            "the same window. This partially reverses the August escalation for Flash."
        ),
        "announced": "2026-09-10",
        "observed": "2026-09-10",
        "effective": "2026-09-10",
        "status": "executed",
        "old_value": "flash off-peak $0.007 / $0.22 / $0.66 (cache-hit / cache-miss / output, per MTok)",
        "new_value": "flash off-peak $0.003 / $0.15 / $0.60 (peak = 2×)",
        "evidence": [
            {
                "type": "capture",
                "capture": "deepseek-updates-2026-09-12",
                "quote": (
                    "Today, we officially release the DeepSeek-V4.1-Flash model. It is the "
                    "smallest model in our new architecture family, with native multimodal "
                    "visual understanding."
                ),
                "label": "changelog entry, 2026-09-10",
            },
            {
                "type": "capture",
                "capture": "deepseek-updates-2026-09-12",
                "quote": "With the release of DeepSeek-V4.1-Flash, API prices have been reduced accordingly.",
            },
            {
                "type": "capture",
                "capture": "deepseek-updates-2026-09-12",
                "quote": (
                    "The previous-generation models V4 Flash and V4 Flash Vision Exp have been "
                    "retired; for compatibility, the model names deepseek-v4-flash and "
                    "deepseek-v4-flash-vision-exp are temporarily routed to V4.1 Flash."
                ),
                "label": "legacy-name retirement",
            },
            {
                "type": "values",
                "capture": "deepseek-pricing-2026-09-12",
                "text": (
                    "Parsed from the live pricing table at capture: flash off-peak cache-hit "
                    "$0.003, cache-miss $0.15, output $0.60 per MTok; peak 2×."
                ),
            },
            {
                "type": "tracking_note",
                "date": "2026-08-31",
                "text": (
                    "Monitoring note: prior basis as of 2026-08-31 — flash off-peak "
                    "$0.007 / $0.22 / $0.66, unchanged since the August 16 escalation."
                ),
            },
        ],
        "notes": [
            "Round trip visible end-to-end: flat → August increase → September cut. Flash off-peak "
            "cache-miss $0.14 → $0.22 → $0.15; output $0.28 → $0.66 → $0.60.",
        ],
    },
    {
        "id": "deepseek-v4pro-continuation",
        "vendor": "deepseek",
        "family": "deepseek-v4-pro",
        "kind": "continuation_notice",
        "title": "DeepSeek V4 Pro API services continue past September 14",
        "summary": (
            "The vendor announced that V4 Pro API services will continue after September 14, "
            "2026, with billing unchanged, citing user demand. The notice references a prior "
            "plan to stop serving V4 Pro; the original discontinuation notice is not in this "
            "watch's captures — that gap is stated rather than filled."
        ),
        "announced": "2026-09-10",
        "observed": "2026-09-10",
        "effective": None,
        "status": "active",
        "old_value": "planned stop of V4 Pro API service after 2026-09-14 (per vendor notice)",
        "new_value": "services continue past 2026-09-14, billing method unchanged",
        "evidence": [
            {
                "type": "capture",
                "capture": "deepseek-updates-2026-09-12",
                "quote": (
                    "In response to user demand, we have decided to continue providing API "
                    "services for DeepSeek V4 Pro after September 14, 2026, with the billing "
                    "method remaining unchanged."
                ),
            },
            {
                "type": "capture",
                "capture": "deepseek-pricing-2026-09-12",
                "quote": (
                    "In response to user demand, we have decided to continue providing API "
                    "services for DeepSeek V4 Pro after September 14, 2026"
                ),
                "label": "same notice carried on the pricing page",
            },
        ],
        "notes": [
            "Documented gap: the original discontinuation notice (implying a September 14 stop) "
            "is not held here, so the change cannot be quoted from both sides.",
        ],
    },
]

# Third-party items for vendors whose pages could not be captured (shown as
# provisional, never as vendor-verified).
PROVISIONAL = [
    {
        "vendor": "openai",
        "date": "2026-08-21",
        "text": (
            "GPT-5.6 Sol API pricing reported cut by more than 20% for three months (through "
            "~November 21); the output component reported cut ~33%."
        ),
        "source": "third-party coverage, as tracked in this watch's monitoring notes",
    },
    {
        "vendor": "openai",
        "date": "2026-07-30",
        "text": "Luna pricing reported cut ~80%; Terra ~20%.",
        "source": "third-party coverage, as tracked in this watch's monitoring notes",
    },
]

# Cross-generation comparisons read directly from the captured tables. These
# are observations, not dated change events.
FAMILY_NOTES = [
    {
        "vendor": "anthropic",
        "text": (
            "Sonnet 5 ($2 / $10) is cheaper than the prior generation Sonnet 4.6 ($3 / $15) — "
            "the long-standing $3/$15 Sonnet tier is broken."
        ),
        "evidence": ["anthropic-docs-2026-09-12"],
    },
    {
        "vendor": "anthropic",
        "text": (
            "Opus pricing fell across generations: the retired Opus 4.1 lists $15 / $75 versus "
            "$5 / $25 for Opus 4.5 through Opus 5 — roughly a 3× cut along the retirement path."
        ),
        "evidence": ["anthropic-docs-2026-09-12"],
    },
    {
        "vendor": "deepseek",
        "text": (
            "Flash round trip: off-peak cache-miss $0.14 (until 2026-08-16) → $0.22 (escalation) "
            "→ $0.15 (2026-09-10); output $0.28 → $0.66 → $0.60."
        ),
        "evidence": ["deepseek-pricing-2026-09-12"],
    },
]

COVERAGE_STATEMENT = (
    "This watch holds vendor-page captures from 2026-09-06 onward, plus dated monitoring notes "
    "from 2026-07-19. \"No reversal found\" is claimable only over the capture interval. "
    "Vendors without a capture are documented gaps, never clean."
)
