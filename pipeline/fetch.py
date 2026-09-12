#!/usr/bin/env python3
"""fetch.py — multi-transport fetch with hard per-source deadlines + receipts.

Evidence rules implemented here (see PROJECT_SPEC.md):
  R2: per-source hard wall-clock deadline (thread + join), multi-transport
      (urllib -> curl fallback). A transport failure is never treated as
      "the page moved" until both transports fail.
  R3: volatile metadata stripped before hashing (canonical JSON hashing).

Usage (CLI):  python3 pipeline/fetch.py <url> <outfile> [--deadline 60]
Prints a JSON receipt: {status, http_code, transport, bytes, sha256, error, attempts}
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import threading
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DEADLINE = 60.0  # seconds, wall clock, per transport attempt
USER_AGENT = "pricing-reversal-watch/1.0 (receipt capture; contact via repository)"

VOLATILE_KEYS = {
    "responseTime",
    "requestTime",
    "request_time",
    "response_time",
    "serverTime",
    "timestamp",
    "generated_at",
    "generatedAt",
}


# ---------------------------------------------------------------- deadline ----

def run_with_deadline(fn, deadline: float):
    """Run fn() in a daemon thread; return (result, error).

    A hanging call becomes a recorded ('timed out') error after `deadline`
    seconds — never a stall, never a crash (S119 rule).
    """
    box: dict = {}

    def worker() -> None:
        try:
            box["result"] = fn()
        except BaseException as exc:  # noqa: BLE001 - recorded, not raised
            box["error"] = f"{type(exc).__name__}: {exc}"

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(deadline)
    if thread.is_alive():
        return None, f"timed out after {deadline:g}s"
    if "error" in box:
        return None, box["error"]
    return box.get("result"), None


# --------------------------------------------------------------- transports ---

def _transport_urllib(url: str, timeout: float) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return {"http_code": resp.status, "bytes": resp.read(), "transport": "urllib"}


def _transport_curl(url: str, timeout: float) -> dict:
    """curl fallback. -L follow redirects, --compressed for gzip.

    Some servers (observed: platform.claude.com) 404 via urllib while curl
    returns 200 on the same URL; some (FRED-class) hang urllib entirely.
    """
    proc = subprocess.run(
        [
            "curl",
            "-s",
            "-L",
            "--compressed",
            "--max-time",
            str(int(timeout)),
            "-A",
            USER_AGENT,
            "-w",
            "\n%{http_code}",
            url,
        ],
        capture_output=True,
        timeout=timeout + 5,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"curl exit {proc.returncode}: {proc.stderr.decode(errors='replace')[:200]}")
    raw = proc.stdout
    # -w appended "\n<http_code>"; split it back off
    body, _, status = raw.rpartition(b"\n")
    try:
        code = int(status.strip())
    except ValueError:
        raise RuntimeError(f"curl produced no http_code (tail={status[:40]!r})")
    return {"http_code": code, "bytes": body, "transport": "curl"}


# ------------------------------------------------------------------- fetch ----

def fetch(url: str, deadline: float = DEFAULT_DEADLINE) -> dict:
    """Fetch url via urllib, falling back to curl. Returns a receipt dict.

    status: "ok" (2xx body captured), "http_error" (transport succeeded, non-2xx),
            "failed" (both transports errored/timed out).
    """
    attempts = []
    last_code = None
    for transport, fn in (("urllib", _transport_urllib), ("curl", _transport_curl)):
        result, err = run_with_deadline(lambda f=fn: f(url, deadline), deadline)
        if err:
            attempts.append({"transport": transport, "error": err})
            continue
        code = result["http_code"]
        attempts.append({"transport": transport, "http_code": code})
        if 200 <= code < 300:
            body = result["bytes"]
            return {
                "status": "ok",
                "http_code": code,
                "transport": transport,
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "attempts": attempts,
                "body": body,
                "error": None,
            }
        last_code = code
    status = "http_error" if last_code else "failed"
    return {
        "status": status,
        "http_code": last_code,
        "transport": None,
        "bytes": 0,
        "sha256": None,
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "attempts": attempts,
        "body": None,
        "error": "; ".join(a.get("error", f"HTTP {a.get('http_code')}") for a in attempts),
    }


# ---------------------------------------------------------------- receipts ----

def save_capture(body: bytes, path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return {"file": str(path), "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ------------------------------------------------------ canonical hashing ----

def strip_volatile(obj, keys=frozenset(VOLATILE_KEYS)):
    """Recursively drop volatile transport keys before hashing (R3)."""
    if isinstance(obj, dict):
        return {k: strip_volatile(v, keys) for k, v in obj.items() if k not in keys}
    if isinstance(obj, list):
        return [strip_volatile(v, keys) for v in obj]
    return obj


def canonical_json_sha256(obj, keys=frozenset(VOLATILE_KEYS)) -> str:
    """Hash a JSON-able object after volatile-key stripping + canonical form."""
    canonical = json.dumps(strip_volatile(obj, keys), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------- CLI ----

def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    url, outfile = argv[1], Path(argv[2])
    deadline = DEFAULT_DEADLINE
    if "--deadline" in argv:
        deadline = float(argv[argv.index("--deadline") + 1])
    receipt = fetch(url, deadline=deadline)
    meta = {k: v for k, v in receipt.items() if k != "body"}
    if receipt["status"] == "ok":
        saved = save_capture(receipt["body"], outfile)
        meta["file"] = saved["file"]
    print(json.dumps(meta, indent=1))
    return 0 if receipt["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
