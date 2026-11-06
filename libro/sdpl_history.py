"""Append-only SDPL availability history: one JSON line per check.

Every writer (daily timer, refresh button, scan) goes through append().
Grows ~200 bytes per book per check (~3-4 MB/year at ~50 books daily).
"""
import json
import time
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "data" / "sdpl_history.jsonl"


def append(book_id: str, title: str, fields: dict, source: str) -> None:
    on_shelf = [b for b in (fields.get("sdpl_on_shelf") or "").split(", ") if b]
    rec = {
        "ts": int(fields.get("sdpl_checked_at") or time.time()),
        "id": book_id,
        "title": title,
        "source": source,                       # timer | refresh | scan | manual
        "found": bool(fields.get("sdpl_found")),
        "status": fields.get("sdpl_status") or "",
        "available": bool(fields.get("sdpl_available")),
        "at_home": bool(fields.get("sdpl_at_home")),
        "copies": int(fields.get("sdpl_copies") or 0),
        "on_shelf_count": len(on_shelf),
    }
    PATH.parent.mkdir(parents=True, exist_ok=True)
    with PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def load(book_id: str | None = None, since: float = 0) -> list[dict]:
    try:
        lines = PATH.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return []
    out = []
    for line in lines:
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("ts", 0) >= since and (book_id is None or r.get("id") == book_id):
            out.append(r)
    return out


def _state(r: dict) -> str:
    if r.get("at_home"):
        return "home"
    if r.get("available"):
        return "requestable"
    return "out" if r.get("found") else "not_held"


_LABELS = {
    ("out", "home"): "★ back on the shelf at your branch",
    ("requestable", "home"): "★ now on the shelf at your branch",
    ("not_held", "home"): "★ newly in the catalog, at your branch",
    ("out", "requestable"): "back on a shelf — request it",
    ("not_held", "requestable"): "newly in the catalog — request it",
    ("not_held", "out"): "newly in the catalog (checked out)",
    ("home", "requestable"): "left your branch's shelf",
    ("home", "out"): "all copies now checked out",
    ("requestable", "out"): "all copies now checked out",
}


def changes(since: float) -> list[dict]:
    """State transitions recorded at or after `since`, newest first."""
    last: dict[str, dict] = {}
    out = []
    for r in sorted(load(), key=lambda r: r["ts"]):
        prev = last.get(r["id"])
        if prev and _state(prev) != _state(r) and r["ts"] >= since:
            a, b = _state(prev), _state(r)
            out.append({"ts": r["ts"], "id": r["id"], "title": r["title"], "from": a, "to": b,
                        "label": _LABELS.get((a, b), f"{a} → {b}"),
                        "good": b == "home" or (b == "requestable" and a != "home")})
        last[r["id"]] = r
    return out[::-1]
