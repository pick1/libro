"""San Diego Public Library physical-availability lookup (Vega Discover API).

The format-group search response already carries per-format availability and
branch locations, so it's one call per book. The catalog asks bots not to
crawl; keep this to one lookup per scanned/refreshed book, never bulk polling.
"""
import os
import re
import time
from difflib import SequenceMatcher
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
_PARTICLES = {"le", "la", "de", "du", "da", "di", "del", "della", "van", "von", "der", "den", "ter", "st"}


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
    if re.fullmatch(r"@?[A-Za-z0-9_.]+", name) and ("_" in name or name.startswith("@") or name.islower()):
        return ""  # social handle (e.g. cj_north_writes), not an author name
    if "," in name:
        part = name.split(",")[0]
    else:
        words = [w for w in re.sub(r"[^\w\s]", " ", name).split() if w.lower() not in _SUFFIXES]
        if not words:
            return ""
        i = len(words) - 1
        while i > 0 and words[i - 1].lower() in _PARTICLES:  # "Le Guin", "van der Meer"
            i -= 1
        part = "".join(words[i:])
    return re.sub(r"[^\w]", "", part.lower())


# "Snow Crash" vs catalog "Snow Crash A Novel": allow a prefix match only when the
# leftover is filler, so "Dune" never matches "Dune Messiah".
_FILLER = re.compile(r"^(or |(a |an )?(novel|novella|memoir|thriller|mystery|romance|story|stories)\b)")


def _title_score(want: str, got: str) -> int:
    """2 = exact, 1 = same title plus filler words, 0 = different book."""
    if want == got:
        return 2
    for short, long_ in ((want, got), (got, want)):
        if long_.startswith(short + " "):
            # filler/alt-title = 1; any other longer title = 0.5, needs the author to confirm
            return 1 if _FILLER.match(long_[len(short) + 1:]) else 0.5
    # spelling variants ("Marvelous" vs "Marvellous"): needs the author to confirm
    if len(want) >= 6 and SequenceMatcher(None, want, got).ratio() >= 0.92:
        return 0.75
    return 0


def _humanize(status: str) -> str:
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", status or "").capitalize()


def search_page_url(title, author=None) -> str:
    return SEARCH_PAGE.format(q=quote(f"{title} {author or ''}".strip()))


def _query_surname(author) -> str:
    """Author's real last word for the search text ("Le Guin" -> "Guin"), unlike the joined match key."""
    a = author or ""
    if "," in a:
        a = a.split(",")[0]
    words = [w for w in re.sub(r"[^\w\s]", " ", a).split() if w.lower() not in _SUFFIXES]
    return words[-1] if words else ""


def _search(text: str, timeout: int) -> list:
    body = {"searchText": text, "sorting": "relevance", "sortOrder": "asc",
            "searchType": "everything", "pageNum": 0, "pageSize": 10, "resourceType": "FormatGroup"}
    r = requests.post(SEARCH_API, json=body, headers=_HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.json().get("data") or []


def check_sdpl(title, author=None, timeout=15) -> dict:
    """Look up one book. Raises requests exceptions on HTTP failure."""
    want_title = _norm_title(title)
    if not want_title:
        return {"found": False, "url": search_page_url(title, author), "checked_at": int(time.time())}
    want_author = _surname(author)
    word = _query_surname(author) if want_author else ""
    results = _search(f"{title} {word}".strip(), timeout)
    if not any(_title_score(want_title, _norm_title(fg.get("title"))) for fg in results):
        results = _search(title, timeout)  # one retry on the title alone
    candidates = []
    for fg in results:
        score = _title_score(want_title, _norm_title(fg.get("title")))
        if not score:
            continue
        got_author = _surname((fg.get("primaryAgent") or {}).get("label"))
        if want_author and got_author and want_author != got_author:
            continue
        if score < 1 and not (want_author and want_author == got_author):
            continue  # loose prefix match only when the author confirms it
        has_book = any(t.get("type") == "physical" and t.get("name") == "Book"
                       for t in fg.get("materialTabs") or [])
        candidates.append((score >= 1, has_book, score, fg))
    if candidates:
        # strong title match first, then a physical Book over CDs/audio, then exactness
        return _summarize(max(candidates, key=lambda c: c[:3])[3])
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
