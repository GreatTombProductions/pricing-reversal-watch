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
        "id": "anthropic-opus55-launch",
        "vendor": "anthropic",
        "family": "Claude Opus 5.5",
        "kind": "new_generation_cut",
        "title": "Opus 5.5 launches at $4/$20 — below the $5/$25 Opus tier",
        "summary": (
            "Claude Opus 5.5 appears on the pricing page at $4 input / $20 output per MTok, 20% "
            "below the $5/$25 that Opus 4.5 through Opus 5 still list. Its cache hits are priced at "
            "0.05× input ($0.20) instead of the usual 0.1× — $0.50 on Opus 5 — and fast mode is "
            "$8/$40 versus $10/$50. Opus 5 stays on the page at its old price: this is a cheaper new "
            "generation, not a cut to an existing model. No launch date is published on the pages "
            "held here; Opus 5.5 is absent from the 2026-09-12 capture and was first seen on "
            "2026-10-04. Sonnet 5.5 launched in the same window at $2/$10, the same price as Sonnet 5."
        ),
        "announced": None,
        "observed": "2026-10-04",
        "confirmed": "2026-10-06",
        "effective": None,
        "status": "active",
        "old_value": "Opus tier $5 / $25 per MTok (Opus 4.5 through Opus 5); cache hit $0.50",
        "new_value": "Opus 5.5 $4 / $20 per MTok; cache hit $0.20 (0.05× input); fast mode $8 / $40",
        "evidence": [
            {
                "type": "capture",
                "capture": "anthropic-docs-2026-10-06",
                "quote": (
                    "On Claude Opus 5.5, a cache hit costs 5% of the standard input price "
                    "($0.20 USD per million tokens)."
                ),
            },
            {
                "type": "capture",
                "capture": "anthropic-docs-2026-10-06",
                "quote": "Cache hits and refreshes on Claude Opus 5.5 are priced at 0.05x the base input price.",
                "label": "footnote on the Opus 5.5 cache-hit price cell",
            },
            {
                "type": "capture",
                "capture": "claude-com-2026-10-06",
                "quote": (
                    "Opus 5.5 Daily driver for agentic coding and enterprise work Prompt caching "
                    "Read $0.20 / MTok Write $5 / MTok Input $4 / MTok Output $20 / MTok"
                ),
                "label": "boundary page, same date",
            },
            {
                "type": "values",
                "capture": "anthropic-docs-2026-10-06",
                "text": (
                    "Parsed from the pricing table at capture: Opus 5.5 input $4, output $20, 5-minute "
                    "cache write $5, 1-hour write $8, cache hit $0.20 per MTok; Opus 5 on the same "
                    "table: $5 / $25 / $6.25 / $10 / $0.50."
                ),
            },
            {
                "type": "tracking_note",
                "date": "2026-10-04",
                "text": (
                    "Monitoring note: Opus 5.5 ($4/$20) and Sonnet 5.5 ($2/$10) first seen on the "
                    "pricing page; neither is in the 2026-09-12 capture. The pricing table was "
                    "re-laid out at the same time (new column order, model taglines, availability "
                    "labels moved into icons)."
                ),
            },
        ],
        "notes": [
            "A cheaper successor is a different shape from a price cut: anyone pinned to Opus 5 "
            "keeps paying $5/$25 until they migrate.",
        ],
    },
    {
        "id": "deepseek-peak-holiday-exclusion",
        "vendor": "deepseek",
        "family": "deepseek-flash / deepseek-v4-pro",
        "kind": "schedule_change",
        "title": "Peak schedule quietly amended — Chinese public holidays now off-peak",
        "summary": (
            "The footnote that defines DeepSeek's peak hours gained a clause: the weekday peak "
            "windows now exclude Chinese public holidays, which are off-peak in full. Rates and "
            "windows are unchanged. The change is not in the API changelog, and no change date is "
            "published: it happened between the 2026-09-12 and 2026-10-06 captures and was first "
            "noticed on 2026-10-04. On a holiday weekday inside a peak window, the same request now "
            "bills at the off-peak rate, which is half the peak rate."
        ),
        "announced": None,
        "observed": "2026-10-04",
        "confirmed": "2026-10-06",
        "effective": None,
        "status": "active",
        "old_value": "peak 01:00–04:00 and 06:00–10:00 UTC, Monday through Friday; all other hours off-peak",
        "new_value": "same windows, Monday through Friday excluding Chinese public holidays; those holidays off-peak in full",
        "evidence": [
            {
                "type": "capture",
                "capture": "deepseek-pricing-2026-09-12",
                "quote": (
                    "Peak hours are 01:00 - 04:00 and 06:00 - 10:00 UTC, Monday through Friday "
                    "(all other hours are off-peak)."
                ),
                "label": "before — 2026-09-12 capture",
            },
            {
                "type": "capture",
                "capture": "deepseek-pricing-2026-10-06",
                "quote": (
                    "Peak hours are 01:00 - 04:00 and 06:00 - 10:00 UTC, Monday through Friday, "
                    "excluding Chinese public holidays. All other hours are off-peak, including "
                    "weekends and Chinese public holidays in full."
                ),
                "label": "after — 2026-10-06 capture",
            },
            {
                "type": "tracking_note",
                "date": "2026-10-04",
                "text": (
                    "Monitoring note: holiday exclusion first seen on the pricing page. The "
                    "2026-10-06 changelog capture contains no entry that mentions holidays."
                ),
            },
        ],
        "notes": [
            "The page does not list which dates count as Chinese public holidays, and this watch "
            "does not supply a holiday calendar.",
        ],
    },
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
                "capture": "anthropic-docs-2026-10-06",
                "quote": (
                    "The $2/$10 per million input/output token pricing for Claude Sonnet 5, "
                    "announced at launch as introductory pricing through August 31, 2026, is now "
                    "the standard price. The previously scheduled increase to $3/$15 per million "
                    "input/output tokens on September 1, 2026 will not occur."
                ),
                "label": (
                    "later capture (2026-10-06), same text — now a footnote on the Sonnet 5 price "
                    "cell (shown as a popover), no longer a visible note above the table"
                ),
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
                "label": (
                    "schedule as captured 2026-09-12 — later amended to exclude Chinese public "
                    "holidays (see the schedule-change event)"
                ),
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
                "label": "same notice carried on the pricing page (2026-09-12)",
            },
            {
                "type": "capture",
                "capture": "deepseek-updates-2026-10-06",
                "quote": (
                    "In response to user demand, we have decided to continue providing API "
                    "services for DeepSeek V4 Pro after September 14, 2026, with the billing "
                    "method remaining unchanged."
                ),
                "label": "still in the API changelog at the 2026-10-06 capture",
            },
            {
                "type": "tracking_note",
                "date": "2026-10-04",
                "text": (
                    "Monitoring note: the continuation notice no longer appears on the pricing "
                    "page (absent from the 2026-10-06 capture, where the footnotes were renumbered). "
                    "It remains in the changelog, and V4 Pro is still listed at unchanged rates."
                ),
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
            "Sonnet 5 and Sonnet 5.5 ($2 / $10) are cheaper than the prior generation Sonnet 4.6 "
            "($3 / $15) — the long-standing $3/$15 Sonnet tier is broken."
        ),
        "evidence": ["anthropic-docs-2026-10-06"],
    },
    {
        "vendor": "anthropic",
        "text": (
            "Opus pricing fell across generations: the retired Opus 4.1 lists $15 / $75, Opus 4.5 "
            "through Opus 5 list $5 / $25, and Opus 5.5 lists $4 / $20 — a 3.75× cut from Opus 4.1 "
            "to Opus 5.5."
        ),
        "evidence": ["anthropic-docs-2026-10-06"],
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
