"""Evidence-rule tests — one per SPEC rule: deadline, multi-transport failure
flagging, canonical hashing, quote verification (fail-closed).

No network access: transports and workers are monkeypatched.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "pipeline"))

import build  # noqa: E402
import fetch as fetch_mod  # noqa: E402


# Rule: per-source hard wall-clock deadline (a hang becomes a recorded error).

def test_deadline_turns_hang_into_recorded_error() -> None:
    def hangs():
        time.sleep(5)
        return "never"

    started = time.monotonic()
    result, err = fetch_mod.run_with_deadline(hangs, deadline=0.2)
    elapsed = time.monotonic() - started
    assert result is None
    assert "timed out" in err
    assert elapsed < 2.0  # returned promptly; did not wait for the hang


def test_deadline_passes_through_fast_results_and_errors() -> None:
    assert fetch_mod.run_with_deadline(lambda: 42, deadline=1.0) == (42, None)

    def boom():
        raise ValueError("kaput")

    result, err = fetch_mod.run_with_deadline(boom, deadline=1.0)
    assert result is None and "kaput" in err


# Rule: multi-transport fallback; both failing = recorded failure (never silent).

def test_fetch_falls_back_to_curl(monkeypatch) -> None:
    def dead_urllib(url, timeout):
        raise RuntimeError("urllib exploded")

    def ok_curl(url, timeout):
        return {"http_code": 200, "bytes": b"<html>ok</html>", "transport": "curl"}

    monkeypatch.setattr(fetch_mod, "_transport_urllib", dead_urllib)
    monkeypatch.setattr(fetch_mod, "_transport_curl", ok_curl)
    receipt = fetch_mod.fetch("https://example.invalid/", deadline=1.0)
    assert receipt["status"] == "ok"
    assert receipt["transport"] == "curl"
    assert receipt["sha256"] == fetch_mod.hashlib.sha256(b"<html>ok</html>").hexdigest()
    assert receipt["attempts"] == [
        {"transport": "urllib", "error": "RuntimeError: urllib exploded"},
        {"transport": "curl", "http_code": 200},
    ]


def test_fetch_both_transports_failing_is_recorded(monkeypatch) -> None:
    def dead(url, timeout):
        raise RuntimeError("nope")

    monkeypatch.setattr(fetch_mod, "_transport_urllib", dead)
    monkeypatch.setattr(fetch_mod, "_transport_curl", dead)
    receipt = fetch_mod.fetch("https://example.invalid/", deadline=1.0)
    assert receipt["status"] == "failed"
    assert receipt["body"] is None
    assert len(receipt["attempts"]) == 2
    assert all("error" in a for a in receipt["attempts"])
    assert "nope" in receipt["error"]


# Rule: volatile keys stripped before hashing.

def test_canonical_hashing_ignores_volatile_and_key_order() -> None:
    a = {"price": 2.0, "responseTime": "t1", "nested": {"x": 1, "requestTime": 99}}
    b = {"nested": {"requestTime": "different", "x": 1}, "responseTime": "t2", "price": 2.0}
    assert fetch_mod.canonical_json_sha256(a) == fetch_mod.canonical_json_sha256(b)
    c = {"price": 3.0}
    assert fetch_mod.canonical_json_sha256(a) != fetch_mod.canonical_json_sha256(c)
    # stripping is recursive, not top-level only
    stripped = fetch_mod.strip_volatile({"nested": {"requestTime": 1, "keep": 2}})
    assert stripped == {"nested": {"keep": 2}}


# Rule: capture quotes verified against captures; fail closed.

def test_verify_quotes_accepts_real_events_and_rejects_fabrication() -> None:
    index = build.load_capture_index()
    assert build.verify_quotes(build.events_mod.EVENTS, index) == []

    bad_events = [
        {
            "id": "fake",
            "evidence": [
                {"type": "capture", "capture": "anthropic-docs-2026-09-12", "quote": "this text was never on the page"},
            ],
        },
        {
            "id": "missing-capture",
            "evidence": [{"type": "capture", "capture": "no-such-capture", "quote": "x"}],
        },
    ]
    failures = build.verify_quotes(bad_events, index)
    assert len(failures) == 2
    assert any("quote not found" in f for f in failures)
    assert any("not available" in f for f in failures)


def test_every_event_has_verifiable_capture_evidence() -> None:
    for ev in build.events_mod.EVENTS:
        caps = [i for i in ev["evidence"] if i["type"] == "capture"]
        assert caps, f"{ev['id']} has no capture evidence"
        assert all(i.get("quote") for i in caps), f"{ev['id']} capture evidence missing quote"
