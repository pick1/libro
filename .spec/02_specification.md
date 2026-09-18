# Libro — Specification
`/speckit.specify`

## Directory structure

```
/home/dp/projects/libro/
├── app.py                  # Streamlit entrypoint
├── libro/
│   ├── __init__.py
│   ├── config.py           # Env vars, paths, constants
│   ├── analyzer.py         # LLM client — copy/adapt from signald/analyzer.py
│   ├── extractor.py        # Web fetch + content cleaning
│   ├── store.py            # ChromaDB want_to_read read/write
│   ├── librarian.py        # Read-only query against ai_librarian books collection
│   └── scrapers.py         # URL fetch, content detection
├── requirements.txt
├── .env.example
├── start.sh
└── libro.service
```

## Features

### F1 — Input handling
- Accept pasted URL or raw text in sidebar text area
- For URLs: fetch with `requests.get`, extract main content via `newspaper3k` or `readability-lxml`
- Truncate to 6000 chars before sending to LLM (match Signal)
- Auto-detect input type: `url` or `text`

### F2 — LLM extraction
Prompt the LLM to extract structured book data. Return JSON only.

**Schema:**
```json
{
  "title": "Exact book title as it appears in the content",
  "author": "Author full name or null",
  "genre_tags": ["2-5 genre tags, specific (e.g. hard sci-fi, solarpunk, cli-fi)"],
  "summary": "2-3 sentence summary of the book — what it's about, tone, why notable",
  "source_type": "url|text",
  "confidence": 0.0,
  "verdict": "One sentence: why you'd want to read this",
  "available_in_cloud_library": false,
  "cloud_library_match": null
}
```

**System prompt:** Book-focused variant of Signal's system prompt. Honest, opinionated.
Instructs model to: extract only books explicitly mentioned, use exact title spelling,
return null for unknown authors, assign specific genre tags (not just "fiction").

### F3 — Cloud Library cross-reference
After LLM extraction, query the AI Librarian `books` ChromaDB collection:
- Embed `f"{title} {author}"` with same `SentenceTransformerEmbeddingFunction`
- `n_results=3`, check top result `relevance_score >= 0.85`
- If match found: set `available_in_cloud_library=True`, `cloud_library_match=<matched title>`
- If no match: both remain false/null

### F4 — ChromaDB storage
Write to `want_to_read` collection in shared vectorstore:
- Create collection if not exists (same embedding function)
- Deduplication: query by title before inserting, skip if `relevance_score >= 0.92`
- Document: `f"{title} by {author}. {summary}"` (for semantic search)
- Metadata: all JSON fields as flat k/v (chromadb metadata must be str/int/float/bool)
- ID: `hashlib.md5(f"{title}{author}".encode()).hexdigest()`

### F5 — Streamlit UI
Match Signal's visual style exactly:

**Sidebar:**
- Libro header (Syne font, `#00ff88` accent)
- Provider selector: OpenCode (primary) / Xavier LAN / Ollama local
- Text area: "Paste a URL or book mention..."
- SCAN button (primary)
- Divider
- Search/filter by genre tag
- Stats: total saved, available in Cloud Library count

**Main feed:**
- Cards matching Signal's card style (`#111118` bg, `border-left` accent)
- Accent color by availability: `#00ff88` if available in Cloud Library, `#4488ff` if not
- Card shows: title, author, genre tags, summary, verdict, availability badge, source, confidence bar
- Delete button per card
- "Available in Cloud Library ✓" badge when matched, with matched title shown

**No auth gate** — libro is local only.

### F6 — Deployment
- `start.sh`: activates venv, runs `streamlit run app.py --server.port 5252`
- `libro.service`: systemd unit, same pattern as `signal.service`
- Cloudflare Tunnel: add `libro.sequoiaanalytics.com` → `localhost:5252`

## LLM client (copy from Signal, adapt)

```python
# libro/analyzer.py

OPENCODE_BASE_URL = "https://opencode.ai/zen/v1"
OPENCODE_API_KEY = os.getenv("OPENCODE_API_KEY", "")
OPENCODE_MODEL = "deepseek-v4-flash-free"

XAVIER_BASE_URL = os.getenv("XAVIER_BASE_URL", "http://192.168.1.110:8080/v1")
XAVIER_API_KEY = os.getenv("XAVIER_API_KEY", "")
XAVIER_MODEL = os.getenv("XAVIER_MODEL", "gpt-oss-20b")

LOCAL_BASE_URL = os.getenv("LOCAL_BASE_URL", "http://localhost:11434/v1")
LOCAL_API_KEY = os.getenv("LOCAL_API_KEY", "ollama")
LOCAL_MODEL = os.getenv("LOCAL_MODEL", "gpt-oss-20b")
```

Fallback chain: OpenCode → Xavier → Ollama local. Each wrapped in try/except,
notify on fallback via callback. Same `parse_json_result()` fence stripper.

## Config / env vars

```
OPENCODE_API_KEY=
XAVIER_BASE_URL=http://192.168.1.110:8080/v1
XAVIER_API_KEY=
XAVIER_MODEL=gpt-oss-20b
LOCAL_BASE_URL=http://localhost:11434/v1
LOCAL_MODEL=gpt-oss-20b
CHROMA_PERSIST_DIR=/home/dp/projects/ai_librarian/vectorstore
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```
