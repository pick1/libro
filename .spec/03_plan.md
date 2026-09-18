# Libro — Technical Plan & Tasks
`/speckit.plan` + `/speckit.tasks`

## Milestones

### M1 — Scaffold
- Create `/home/dp/projects/libro/` structure
- `config.py` with all env vars and paths
- `requirements.txt` (see below)
- `.env.example`
- Empty `libro/__init__.py`
- Verify ChromaDB vectorstore path is reachable and `books` collection loads

### M2 — LLM Client (`libro/analyzer.py`)
- Copy `analyze_with_openai()` and `parse_json_result()` from `signald/analyzer.py`
- Wire three-provider chain: OpenCode → Xavier → Ollama
- Write `BOOK_SYSTEM_PROMPT` (book extraction variant)
- Write `build_book_prompt(content, source_hint)` 
- Write `extract_book(content, source_hint, provider_config) -> dict`
- Test: point at OpenCode, paste a book review URL content, confirm JSON output

### M3 — Storage (`libro/store.py` + `libro/librarian.py`)
**store.py — want_to_read collection:**
- `pysqlite3` swap at top
- `WantToReadStore` class: `__init__` loads/creates `want_to_read` collection
- `add(book: dict) -> bool` — dedup check then insert
- `all() -> list[dict]` — return all entries as list of metadata dicts
- `delete(id: str)` — remove by ID
- `search(query: str, k=10) -> list[dict]` — semantic search

**librarian.py — read-only books collection:**
- `LibrarianIndex` class: loads `books` collection read-only
- `check_availability(title: str, author: str) -> tuple[bool, str | None]`
  — embeds query, top-3 results, threshold 0.85, returns (available, matched_title)

### M4 — Web Extraction (`libro/extractor.py`)
- `fetch_url(url: str) -> str` — requests.get, newspaper3k Article extraction
- `clean_text(text: str) -> str` — strip excess whitespace, truncate to 6000 chars
- `detect_source_type(input: str) -> str` — "url" if starts with http, else "text"

### M5 — Streamlit UI (`app.py`)
- Dark theme CSS matching Signal (DM Mono, Syne, `#111118`, `#00ff88`)
- Sidebar: provider selector, text area, SCAN button, search, stats
- `render_card(entry)` — availability-colored border, title/author/genres/summary/verdict/confidence bar
- Main feed: load all from `WantToReadStore`, filter by search/genre
- Analysis trigger: fetch → extract → availability check → store → rerun
- Delete button per card

### M6 — Deployment
- `start.sh` — venv activate + `streamlit run app.py --server.port 5252`
- `libro.service` — systemd unit (copy from `signal.service`, adjust paths/port)
- README with setup, env vars, Cloudflare Tunnel instructions
- Add `libro.sequoiaanalytics.com → localhost:5252` to Cloudflare Tunnel config

---

## Requirements

```
streamlit>=1.35
requests
newspaper3k
lxml[html_clean]
chromadb
pysqlite3-binary
sentence-transformers
python-dotenv
```

---

## Critical implementation notes

1. **pysqlite3 swap must be first** in any file that imports chromadb:
   ```python
   try:
       import pysqlite3
       sys.modules["sqlite3"] = pysqlite3
   except ImportError:
       pass
   ```

2. **Never write to `books` collection** — `LibrarianIndex` opens it with
   `client.get_collection()` only, never `get_or_create_collection()`

3. **ChromaDB metadata values must be primitives** — flatten all nested structures
   before storing. `genre_tags` list → store as comma-separated string, split on retrieval.

4. **Embedding model must match AI Librarian exactly:**
   `sentence-transformers/all-MiniLM-L6-v2`, `device="cpu"`
   Using a different model would make cross-collection similarity scores meaningless.

5. **Availability threshold:** 0.85 relevance score. ChromaDB returns distances
   (lower = closer); Signal's librarian converts: `relevance = 1 - distance`.
   Check `relevance_score >= 0.85`.

6. **Port 5252** — confirm not in use on floorBoard before deploying.

7. **OpenCode API key** — same key used in Signal. Copy from Signal's `.env`.
