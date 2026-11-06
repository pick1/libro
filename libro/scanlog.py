"""Per-scan audit log: one JSON line per SCAN (ok / empty / error).

Own logger, propagate=False, size-capped rotation, so third-party DEBUG
chatter can never land here or grow it unbounded.
"""
import json
import logging
import traceback
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent.parent / "data" / "scans.jsonl"

_logger = logging.getLogger("libro.scans")
if not _logger.handlers:  # Streamlit reruns re-import; don't stack handlers
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _h = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    _h.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(_h)
    _logger.setLevel(logging.INFO)
    _logger.propagate = False


def log_scan(*, user_input, source_type, stage, status, books=None, error=None):
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,            # ok | empty | error
        "stage": stage,              # detect | fetch | clean | extract | store | done
        "source_type": source_type,
        "input": (user_input or "").strip()[:500],
    }
    if books is not None:
        rec["books"] = books
    if error is not None:
        rec["error_type"] = type(error).__name__
        rec["error"] = str(error)[:1000]
        rec["traceback"] = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )[-4000:]
    _logger.info(json.dumps(rec, ensure_ascii=False))


def recent(n=20, status=None):
    try:
        lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return []
    rows = []
    for line in lines:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if status:
        rows = [r for r in rows if r.get("status") == status]
    return rows[-n:][::-1]
