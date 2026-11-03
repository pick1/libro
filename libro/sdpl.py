"""San Diego Public Library physical-availability lookup (Vega Discover API).

The format-group search response already carries per-format availability and
branch locations, so it's one call per book. The catalog asks bots not to
crawl; keep this to one lookup per scanned/refreshed book, never bulk polling.
"""
import os
import re
import time
from urllib.parse import quote

import requests

try:  # pick up SDPL_HOME_BRANCH from .env if python-dotenv is installed
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

CUSTOMER = "sdpl.na5.iiivega.com"
SEARCH_API = "https://na5.iiivega.com/api/search-result/search/format-groups"
CARD_URL = "https://" + CUSTOMER + "/search/card?id={id}&entityType=FormatGroup"
SEARCH_PAGE = "https://" + CUSTOMER + "/search?query={q}&searchType=everything&pageSize=10"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Libro/1.0",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "api-version": "2",
    "iii-customer-domain": CUSTOMER,
    "iii-host-domain": CUSTOMER,
    "Origin": "https://" + CUSTOMER,
    "Referer": "https://" + CUSTOMER + "/",
}
_SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "phd"}


def home_branch() -> str:
    """e.g. SDPL_HOME_BRANCH=College-Rolando in .env (matched case-insensitively)."""
    return os.getenv("SDPL_HOME_BRANCH", "").strip()


def _norm_title(t):
    t = (t or "").lower().split(":")[0]
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return re.sub(r"^(the|a|an) ", "", t)


def _surname(name):
    name = (name or "").strip()
    if not name:
        return ""
    if "," in name:
        part = name.split(",")[0]
    else:
        words = [w for w in re.sub(r"[^\w\s]", " ", name).split() if w.lower() not in _SUFFIXES]
        part = words[-1] if words else ""
    return re.sub(r"[^\w]", "", part.lower())


# "Snow Crash" vs catalog "Snow Crash A Novel": allow a prefix match only when the
# leftover is filler, so "Dune" never matches "Dune Messiah".
_FILLER = re.compile(r"^(a |an )?(novel|novella|memoir|thriller|mystery|romance|story|stories)\b")


def _title_score(want: str, got: str) -> int:
    """2 = exact, 1 = same title plus filler words, 0 = different book."""
    if want == got:
        return 2
    for short, long_ in ((want, got), (got, want)):
        if long_.startswith(short + " ") and _FILLER.match(long_[len(short) + 1:]):
            return 1
    return 0


def _humanize(status: str) -> str:
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", status or "").capitalize()


def search_page_url(title, author=None) -> str:
    return SEARCH_PAGE.format(q=quote(f"{title} {author or ''}".strip()))


def check_sdpl(title, author=None, timeout=15) -> dict:
    """Look up one book. Raises requests exceptions on HTTP failure."""
    want_title = _norm_title(title)
    if not want_title:
        return {"found": False, "url": search_page_url(title, author), "checked_at": int(time.time())}
    want_author = _surname(author)
    body = {"searchText": f"{title} {want_author}".strip(), "sorting": "relevance",
            "sortOrder": "asc", "searchType": "everything", "pageNum": 0,
            "pageSize": 5, "resourceType": "FormatGroup"}
    r = requests.post(SEARCH_API, json=body, headers=_HEADERS, timeout=timeout)
    r.raise_for_status()
    best, best_score = None, 0
    for fg in r.json().get("data") or []:
        score = _title_score(want_title, _norm_title(fg.get("title")))
        if not score:
            continue
        got_author = _surname((fg.get("primaryAgent") or {}).get("label"))
        if want_author and got_author and want_author != got_author:
            continue
        if score > best_score:
            best, best_score = fg, score
            if score == 2:
                break
    if best:
        return _summarize(best)
    return {"found": False, "url": search_page_url(title, author), "checked_at": int(time.time())}


def _summarize(fg: dict) -> dict:
    base = {"found": True, "id": fg.get("id") or "", "url": CARD_URL.format(id=fg.get("id")),
            "match": fg.get("title") or "", "checked_at": int(time.time())}
    tabs = fg.get("materialTabs") or []
    physical = [t for t in tabs if t.get("type") == "physical"]
    if not physical:
        formats = ", ".join(sorted({t["name"] for t in tabs if t.get("name")})) or "digital"
        return {**base, "physical": False, "available": False,
                "status": f"{formats} only", "summary": f"SDPL: {formats} only"}

    tab = next((t for t in physical if t.get("name") == "Book"), physical[0])
    status = _humanize(((tab.get("availability") or {}).get("status") or {}).get("general") or "Unknown")
    copies = tab.get("itemCount") or 0
    locs = tab.get("locations") or []
    shelf = [l["label"] for l in locs if l.get("availabilityStatus") == "Available" and l.get("label")]
    total = tab.get("locationsTotalResults") or len(locs)
    partial = bool(tab.get("hasMoreLocations")) and total > len(locs)

    if shelf:
        where = ", ".join(s.replace(" Library", "") for s in shelf[:3])
        if len(shelf) > 3:
            where += f" +{len(shelf) - 3}"
        summary = f"SDPL: on shelf at {where}"
    else:
        summary = f"SDPL: {status}"
    if copies:
        summary += f" · {copies} {'copy' if copies == 1 else 'copies'}"
    if tab.get("name") != "Book":
        summary += f" ({tab.get('name')})"

    return {**base, "physical": True, "format": tab.get("name") or "",
            "available": bool(shelf) or status.lower() == "available",
            "status": status, "copies": copies, "on_shelf": shelf,
            "branches_total": total, "partial": partial,
            "call_number": tab.get("callNumber") or "",
            "shelf_location": tab.get("itemShelfLocation") or "",
            "summary": summary}


def as_fields(result: dict | None) -> dict:
    """Flatten to scalar sdpl_* fields for the store."""
    r = result or {}
    on_shelf = r.get("on_shelf") or []
    home = home_branch().lower()
    at_home = bool(home) and any(home in b.lower() for b in on_shelf)
    return {
        "sdpl_checked_at": r.get("checked_at") or int(time.time()),
        "sdpl_found": bool(r.get("found")),
        "sdpl_physical": bool(r.get("physical")),
        "sdpl_available": bool(r.get("available")),
        "sdpl_at_home": at_home,
        "sdpl_status": r.get("status") or ("Not held" if r else ""),
        "sdpl_format": r.get("format") or "",
        "sdpl_copies": int(r.get("copies") or 0),
        "sdpl_on_shelf": ", ".join(on_shelf),
        "sdpl_branches_total": int(r.get("branches_total") or 0),
        "sdpl_locations_partial": bool(r.get("partial")),
        "sdpl_call_number": r.get("call_number") or "",
        "sdpl_shelf_location": r.get("shelf_location") or "",
        "sdpl_record_id": r.get("id") or "",
        "sdpl_url": r.get("url") or "",
        "sdpl_summary": r.get("summary") or ("Not in SDPL catalog" if r else ""),
    }
