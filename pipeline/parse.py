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
import json
import re

# ------------------------------------------------------------------ helpers ---

def capture_text(doc: str) -> str:
    """The vendor words a capture carries, for quote verification.

    Visible text (scripts stripped) plus vendor notes that the page renders
    from its serialized component tree (price-cell footnotes, model status
    popovers). Those notes are on the page a reader sees — only as popovers —
    so a quote found there is a vendor quote, labeled by where it appears.
    """
    parts = [_text(_strip_scripts(doc))]
    parts += [n["text"] for n in _anthropic_cell_notes(doc)]
    parts += [n["explanation"] for n in _anthropic_model_notes(doc).values()]
    return " ".join(" ".join(parts).split())


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


class ParseError(ValueError):
    """A page no longer matches the structure a parser was written against.

    Raised instead of guessing: a layout change must stop the build, never
    publish values read from the wrong column.
    """


def _raw_rows(table: str) -> list[list[str]]:
    out = []
    for row in re.findall(r"<tr.*?</tr>", table, flags=re.S):
        out.append(re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, flags=re.S))
    return out


def _rows(table: str) -> list[list[str]]:
    return [[_text(c) for c in row] for row in _raw_rows(table)]


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

# Column labels seen on the Model pricing table, by layout generation.
# 2026-09 layout: one header row
#   Model | Base input tokens | 5m cache writes | 1h cache writes | Cache hits and refreshes | Output tokens
# 2026-10 layout: a group row (Model | Base tokens | Prompt caching) above
#   Name | Input | Output | 5m writes | 1h writes | Hits and refreshes
# Columns are located by label, never by position. A missing label raises.
ANTHROPIC_COLUMNS = {
    "name": ("model", "name"),
    "input": ("base input tokens", "input"),
    "output": ("output tokens", "output"),
    "cache_write_5m": ("5m cache writes", "5m writes"),
    "cache_write_1h": ("1h cache writes", "1h writes"),
    "cache_hit": ("cache hits and refreshes", "hits and refreshes"),
}


def _anthropic_column_map(label_row: list[str]):
    """Return {field: index} if every field has exactly one matching label."""
    labels = [c.strip().lower() for c in label_row]
    found = {}
    for field, accepted in ANTHROPIC_COLUMNS.items():
        hits = [i for i, lab in enumerate(labels) if lab in accepted]
        if len(hits) != 1:
            return None
        found[field] = hits[0]
    return found


def _anthropic_name_cell(cell_html: str) -> dict:
    """Split a model-name cell into name, vendor tagline and status labels.

    2026-09 pages put status inline: "Claude Haiku 3.5 ( retired, except on
    Bedrock and Google Cloud )". 2026-10 pages put a tagline in a caption span
    and status in an icon button's aria-label: "Claude Opus 4.1 (Retired)".
    Status labels are kept verbatim; nothing is inferred.
    """
    flags = []
    for label in re.findall(r'aria-label="[^"]*\(([^)]+)\)"', cell_html):
        flags.append(htmlmod.unescape(label).strip())
    description = None
    mdesc = re.search(r'<span[^>]*class="[^"]*text-caption[^"]*"[^>]*>(.*?)</span>', cell_html, flags=re.S)
    if mdesc:
        description = _text(mdesc.group(1)) or None
        cell_html = cell_html[: mdesc.start()] + cell_html[mdesc.end() :]
    cell_html = re.sub(r"<button.*?</button>", " ", cell_html, flags=re.S)
    text = _text(cell_html)
    for inline in re.findall(r"\(\s*(limited availability|retired[^)]*?)\s*\)", text):
        flags.append(inline.strip())
    name = re.sub(r"\s*\(\s*(limited availability|retired[^)]*?)\s*\)", "", text).strip()
    return {"name": name, "description": description, "flags": flags}


def _flight_payload(doc: str) -> str:
    """Concatenate the decoded self.__next_f.push([1, "..."]) string chunks."""
    chunks = []
    for m in re.finditer(r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)', doc):
        try:
            chunks.append(json.loads(m.group(1)))
        except ValueError:
            continue
    return "".join(chunks)


def _anthropic_cell_notes(doc: str) -> list[dict]:
    """Footnotes attached to price cells, read from the page's flight payload.

    The 2026-10 layout moved vendor notes (e.g. the Sonnet 5 cancellation)
    out of visible callouts into a popover on the price cell; the text exists
    only in the serialized component tree inside <script>. Each note is kept
    verbatim with its anchor id.
    """
    payload = _flight_payload(doc)
    by_text: dict[str, dict] = {}
    for m in re.finditer(r'"notes":(\[(?:"(?:[^"\\]|\\.)*",?)+\]),"anchorId":"([^"]+)"', payload):
        try:
            texts = json.loads(m.group(1))
        except ValueError:
            continue
        anchor = None if m.group(2).startswith("$") else m.group(2)
        for text in texts:
            text = " ".join(str(text).split())
            entry = by_text.setdefault(text, {"anchor": anchor, "text": text})
            if entry["anchor"] is None and anchor:
                entry["anchor"] = anchor
    return list(by_text.values())


def _anthropic_model_notes(doc: str) -> dict:
    """Per-model status popovers: {name: {kind, label, explanation}} (2026-10 layout)."""
    payload = _flight_payload(doc)
    out = {}
    pattern = r'\{"name":"([^"]+)","note":\{"kind":"([^"]*)","label":"([^"]*)","explanation":("(?:[^"\\]|\\.)*")'
    for m in re.finditer(pattern, payload):
        try:
            explanation = json.loads(m.group(4))
        except ValueError:
            continue
        out.setdefault(m.group(1), {"kind": m.group(2), "label": m.group(3), "explanation": " ".join(explanation.split())})
    return out


def parse_anthropic(doc: str) -> dict:
    body = _strip_scripts(doc)
    heads = _heading_map(body)

    models = []
    model_notes = _anthropic_model_notes(doc)
    table_found = False
    for m in re.finditer(r"<table.*?</table>", body, flags=re.S):
        if _section_for(m.start(), heads) != "Model pricing":
            continue
        raw = _raw_rows(m.group(0))
        rows = [[_text(c) for c in r] for r in raw]
        label_idx, cols = None, None
        for i, row in enumerate(rows[:3]):
            cols = _anthropic_column_map(row)
            if cols:
                label_idx = i
                break
        if cols is None:
            continue
        table_found = True
        width = len(rows[label_idx])
        for raw_row, row in zip(raw[label_idx + 1 :], rows[label_idx + 1 :]):
            if len(row) != width:
                continue  # group rows such as "Additional models"
            name = _anthropic_name_cell(raw_row[cols["name"]])
            prices = {f: _price(row[i]) for f, i in cols.items() if f != "name"}
            missing = [f for f, v in prices.items() if v is None]
            if missing:
                raise ParseError(f"Model pricing row {name['name']!r}: no price in {missing}")
            note = model_notes.get(name["name"])
            if note:
                # the popover's own wording carries the detail the icon label drops
                # ("Retired" -> "retired, except on Bedrock and Google Cloud.")
                label = note["label"].strip().lower()
                expl = note["explanation"].rstrip(".")
                name["flags"] = [expl if (f.lower() == label and expl.lower().startswith(label)) else f for f in name["flags"]]
            retired = [f for f in name["flags"] if f.lower().startswith("retired")]
            models.append(
                {
                    "name": name["name"],
                    "description": name["description"],
                    **prices,
                    "flags": name["flags"],
                    "status_note": note["explanation"] if note else None,
                    "retired": bool(retired),
                }
            )
        break

    if not table_found:
        raise ParseError("Model pricing table with recognizable column labels not found")
    if not models:
        raise ParseError("Model pricing table parsed to zero model rows")

    callouts = []
    for m in re.finditer(r'<aside[^>]*role="note"[^>]*>(.*?)</aside>', body, flags=re.S):
        callouts.append(_text(m.group(1)))

    return {"models": models, "callouts": callouts, "cell_notes": _anthropic_cell_notes(doc)}


# -------------------------------------------------- claude.com (boundary) ----

_CC_BLOCK = re.compile(r"Input \$([\d.,]+) / MTok Output \$([\d.,]+) / MTok")
_CC_NAME = re.compile(r"\b(Fable|Mythos|Opus|Sonnet|Haiku)(?: (\d+(?:\.\d+)?))?\b(?!\.\d)")


def parse_claude_com(doc: str) -> dict:
    """Price blocks from the subscription/boundary page.

    Each "Input $a / MTok Output $b / MTok" block is attributed to the LAST
    model name that appears between the previous block and this one — a
    boundary-aware match, so "Opus 5" never matches inside "Opus 5.5".
    """
    body = _strip_scripts(doc)
    text = _text(body)
    blocks = []
    prev_end = 0
    for m in _CC_BLOCK.finditer(text):
        names = list(_CC_NAME.finditer(text, prev_end, m.start()))
        prev_end = m.end()
        if not names:
            continue
        nm = names[-1]
        name = nm.group(1) + (" " + nm.group(2) if nm.group(2) else "")
        blocks.append(
            {
                "name": name,
                "input": float(m.group(1).replace(",", "")),
                "output": float(m.group(2).replace(",", "")),
                "context": text[max(0, nm.start() - 60) : m.end()],
            }
        )
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
    stop = area.find("Deduction Rules")
    if stop != -1:
        area = area[:stop]
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
    # The operative schedule can span two sentences: the 2026-10 page adds
    # "All other hours are off-peak, including weekends and Chinese public
    # holidays in full." after the window sentence. Keep both, verbatim.
    sm = re.search(r"Peak hours are [^.]+\.(?:\s*All other hours [^.]+\.)?", text)
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
