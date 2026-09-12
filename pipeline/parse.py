#!/usr/bin/env python3
"""parse.py — parsers for vendor semantic-authority pages (pure functions over HTML).

Every parser returns a plain dict of declared values; nothing here interprets
or averages. Values absent from a page stay absent (None), never zero-filled.

Parsers:
  parse_anthropic(html)        -> model pricing table + note callouts
  parse_claude_com(html)       -> boundary artifact price blocks (subscription page)
  parse_deepseek_pricing(html) -> model table + rate bands + footnotes
  parse_deepseek_updates(html) -> dated changelog entries
"""
from __future__ import annotations

import html as htmlmod
import re

# ------------------------------------------------------------------ helpers ---

def _strip_scripts(doc: str) -> str:
    return re.sub(r"<script.*?</script>", "", doc, flags=re.S)


_INVISIBLE = re.compile(r"[\u200b-\u200f\ufeff\ue000-\uf8ff]")


def _text(el: str) -> str:
    """Tag-stripped, entity-decoded text with zero-width/PUA glyphs removed.

    Vendor pages carry zero-width spaces after headings and icon-font glyphs
    in asides; both break naive equality checks and quote boundaries.
    """
    raw = htmlmod.unescape(re.sub(r"<[^>]+>", " ", el))
    return " ".join(_INVISIBLE.sub("", raw).split())


def _tables(doc: str) -> list[str]:
    return re.findall(r"<table.*?</table>", doc, flags=re.S)


def _rows(table: str) -> list[list[str]]:
    out = []
    for row in re.findall(r"<tr.*?</tr>", table, flags=re.S):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, flags=re.S)
        out.append([_text(c) for c in cells])
    return out


def _price(cell: str):
    """'$12.50 / MTok 1' -> 12.5 ; None when no dollar amount."""
    m = re.search(r"\$([\d,]+(?:\.\d+)?)", cell)
    if not m:
        return None
    return float(m.group(1).replace(",", ""))


def _heading_map(body: str):
    """Return list of (position, level, text) for h1..h6."""
    heads = []
    for m in re.finditer(r"<h([1-6])[^>]*>(.*?)</h\1>", body, flags=re.S):
        heads.append((m.start(), int(m.group(1)), _text(m.group(2))))
    return heads


def _section_for(pos: int, heads) -> str:
    label = ""
    for hpos, level, text in heads:
        if hpos < pos:
            label = text
        else:
            break
    return label


# ---------------------------------------------------------------- Anthropic ---

def parse_anthropic(doc: str) -> dict:
    body = _strip_scripts(doc)
    heads = _heading_map(body)

    models = []
    for m in re.finditer(r"<table.*?</table>", body, flags=re.S):
        section = _section_for(m.start(), heads)
        if section != "Model pricing":
            continue
        rows = _rows(m.group(0))
        if not rows:
            continue
        header = rows[0]
        if not header or header[0] != "Model":
            continue
        for row in rows[1:]:
            if len(row) < 6:
                continue
            name_raw = row[0]
            limited = "( limited availability )" in name_raw
            retired_note = None
            mret = re.search(r"\( retired, except on ([^)]+)\)", name_raw)
            if mret:
                retired_note = f"retired, except on {mret.group(1)}"
            clean = re.sub(r"\s*\(( limited availability|retired[^)]*)\)", "", name_raw).strip()
            models.append(
                {
                    "name": clean,
                    "input": _price(row[1]),
                    "cache_write_5m": _price(row[2]),
                    "cache_write_1h": _price(row[3]),
                    "cache_hit": _price(row[4]),
                    "output": _price(row[5]),
                    "limited": limited,
                    "retired_note": retired_note,
                }
            )
        break

    callouts = []
    for m in re.finditer(r'<aside[^>]*role="note"[^>]*>(.*?)</aside>', body, flags=re.S):
        callouts.append(_text(m.group(1)))

    return {"models": models, "callouts": callouts}


# -------------------------------------------------- claude.com (boundary) ----

def parse_claude_com(doc: str) -> dict:
    body = _strip_scripts(doc)
    text = _text(body)
    blocks = []
    for name in ["Fable", "Mythos", "Opus 5", "Sonnet 5", "Haiku 4.5"]:
        for m in re.finditer(re.escape(name), text):
            idx = m.start()
            window = text[idx : idx + 700]
            pm = re.search(r"Input \$([\d.,]+) / MTok Output \$([\d.,]+) / MTok", window)
            if pm:
                blocks.append(
                    {
                        "name": name,
                        "input": float(pm.group(1)),
                        "output": float(pm.group(2)),
                        "context": text[max(0, idx - 60) : idx + 160],
                    }
                )
    # de-duplicate identical (name, input, output) observations
    seen, unique = set(), []
    for b in blocks:
        key = (b["name"], b["input"], b["output"])
        if key not in seen:
            seen.add(key)
            unique.append(b)
    return {"price_blocks": unique}


# ---------------------------------------------------------------- DeepSeek ----

_BAND_SECTIONS = {
    "1M INPUT TOKENS (CACHE HIT)": "cache_hit",
    "1M INPUT TOKENS (CACHE MISS)": "cache_miss",
    "1M OUTPUT TOKENS": "output",
}


def parse_deepseek_pricing(doc: str) -> dict:
    body = _strip_scripts(doc)
    tables = _tables(body)
    if not tables:
        return {"models": [], "footnotes": [], "schedule_quote": None}
    rows = _rows(tables[0])

    model_names: list[str] = []
    versions: list[str] = []
    rates: list[dict] = []
    current_section = None
    for row in rows:
        if not row:
            continue
        if row[0] == "MODEL" and len(row) >= 3:
            model_names = [re.sub(r"\s*\(\d+\)$", "", c) for c in row[1:]]
            rates = [{"off_peak": {}, "peak": {}} for _ in model_names]
        elif row[0] == "MODEL VERSION" and len(row) >= 3:
            versions = row[1:]
        elif len(row) >= 5 and row[1] in _BAND_SECTIONS and row[2] in ("OFF-PEAK", "PEAK"):
            # 5-cell variant: ['PRICING (3)', '1M INPUT TOKENS (CACHE HIT)', 'OFF-PEAK', '$a', '$b']
            current_section = _BAND_SECTIONS[row[1]]
            band = "off_peak" if row[2] == "OFF-PEAK" else "peak"
            for i, cell in enumerate(row[3:]):
                if i < len(rates):
                    rates[i][band][current_section] = _price(cell)
        elif len(row) >= 4 and row[0] in _BAND_SECTIONS and row[1] in ("OFF-PEAK", "PEAK"):
            # 4-cell variant: ['1M INPUT TOKENS (CACHE MISS)', 'OFF-PEAK', '$a', '$b']
            current_section = _BAND_SECTIONS[row[0]]
            band = "off_peak" if row[1] == "OFF-PEAK" else "peak"
            for i, cell in enumerate(row[2:]):
                if i < len(rates):
                    rates[i][band][current_section] = _price(cell)
        elif len(row) >= 3 and row[0] in ("OFF-PEAK", "PEAK") and current_section:
            # continuation: ['PEAK', '$a', '$b']
            band = "off_peak" if row[0] == "OFF-PEAK" else "peak"
            for i, cell in enumerate(row[1:]):
                if i < len(rates):
                    rates[i][band][current_section] = _price(cell)

    models = []
    for i, name in enumerate(model_names):
        models.append(
            {
                "id": name,
                "version": versions[i] if i < len(versions) else None,
                "rates": rates[i] if i < len(rates) else {"off_peak": {}, "peak": {}},
            }
        )

    # concurrency limit row
    for row in rows:
        if row and row[0].startswith("Concurrency Limit") and len(row) >= 3:
            for i, cell in enumerate(row[1:]):
                if i < len(models):
                    models[i]["concurrency_limit"] = cell

    text = _text(body)
    footnotes = []
    marker = text.rfind("Concurrency Limit", 0, text.find("Deduction Rules")) if "Deduction Rules" in text else -1
    area = text[marker:] if marker != -1 else text
    positions = {}
    for n in range(1, 5):
        # rfind: the footnote zone is the last stretch of the page; the table
        # itself also carries "(1)".."(4)" markers, but those come earlier.
        pos = area.rfind(f"({n}) ")
        if pos != -1:
            positions[n] = pos
    for n, pos in sorted(positions.items()):
        later = [p for k, p in positions.items() if k != n and p > pos]
        end = min(later) if later else len(area)
        footnotes.append({"n": n, "text": area[pos + len(f"({n}) ") : end].strip()})
    schedule_quote = None
    sm = re.search(r"Peak hours are [^.]+\.", text)
    if sm:
        schedule_quote = sm.group(0)
    return {"models": models, "footnotes": footnotes, "schedule_quote": schedule_quote}


def parse_deepseek_updates(doc: str) -> dict:
    body = _strip_scripts(doc)
    raw_text = " ".join(htmlmod.unescape(re.sub(r"<[^>]+>", " ", body)).split())
    entries = []
    matches = list(re.finditer(r"Date:\s*(\d{4}-\d{2}-\d{2})", raw_text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else min(len(raw_text), m.start() + 4000)
        chunk = raw_text[m.start() : end].strip()
        after_date = chunk[len(m.group(0)) :]
        # vendor pages separate date/title/body with zero-width spaces; the
        # first zero-width-delimited segment after the date is the headline.
        segments = [_INVISIBLE.sub("", s).strip() for s in re.split(r"[\u200b-\u200f]", after_date)]
        segments = [s for s in segments if s]
        title = segments[0] if segments else after_date[:100]
        entries.append({"date": m.group(1), "title": title, "text": _text(chunk)})
    return {"entries": entries}
