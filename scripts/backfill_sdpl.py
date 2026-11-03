"""Fill or refresh SDPL availability for books already in the list.

  venv/bin/python scripts/backfill_sdpl.py            # only never-checked books
  venv/bin/python scripts/backfill_sdpl.py --all      # re-check everything
  venv/bin/python scripts/backfill_sdpl.py --limit 1  # try one first
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from libro.filters import book_id
from libro.sdpl import as_fields, check_sdpl
from libro.store import WantToReadStore

ap = argparse.ArgumentParser()
ap.add_argument("--all", action="store_true")
ap.add_argument("--limit", type=int, default=0)
args = ap.parse_args()

store = WantToReadStore()
books = [b for b in store.all() if args.all or not b.get("sdpl_checked_at")]
if args.limit:
    books = books[: args.limit]
print(f"{len(books)} book(s) to check")

for i, b in enumerate(books, 1):
    try:
        f = as_fields(check_sdpl(b["title"], b.get("author")))
        store.update_fields(book_id(b), f)
        star = "★" if f["sdpl_at_home"] else " "
        print(f"[{i}/{len(books)}] {star} {b['title'][:40]:40} {f['sdpl_summary']}")
    except Exception as e:
        print(f"[{i}/{len(books)}] ! {b['title'][:40]:40} {type(e).__name__}: {e}")
    time.sleep(2)
