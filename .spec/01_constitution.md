# Libro — Constitution
`/speckit.constitution`

## Project

**Libro** — A personal book discovery and want-to-read tracker that extracts book metadata
from web articles and pasted text, categorizes by genre, stores in a ChromaDB
`want_to_read` collection, and cross-references against the existing AI Librarian
catalog to surface Cloud Library availability.

## Location

`/home/dp/projects/libro/`

## Inference backend

- **Primary:** OpenCode (`https://opencode.ai/zen/v1`, model: `deepseek-v4-flash-free`)
- **Fallback:** Xavier LAN (`http://192.168.1.110:8080/v1`, model: `gpt-oss-20b`)
- **Local fallback:** Ollama (`http://localhost:11434/v1`, model: `gpt-oss-20b`)
- All providers use the same `requests.post` OpenAI-compatible client pattern from Signal (`signald/analyzer.py`)
- Bearer token auth, 120s timeout, `parse_json_result()` for fence stripping

## Storage

- **Want-to-read list:** ChromaDB `want_to_read` collection
- **Vectorstore path:** `/home/dp/projects/ai_librarian/vectorstore/` (shared with AI Librarian — do NOT create a new one)
- **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` via `SentenceTransformerEmbeddingFunction`, device=cpu
- **pysqlite3 swap:** Required at top of any file importing chromadb (copy pattern from `ai_librarian/backend/rag.py`)
- No SQLite, no TinyDB — ChromaDB only

## AI Librarian integration

- After extracting a book, run a semantic search against the existing `books` collection
- Attach `available_in_cloud_library: bool` and `cloud_library_match: str | None` (matched title) to every entry
- Do not modify the `books` collection — read only

## Core principles

- Local-first: OpenCode primary, Xavier fallback, Ollama last resort
- Single source of truth: one shared ChromaDB vectorstore at the AI Librarian path
- Signal-consistent: same LLM client pattern, same dark Streamlit aesthetic (DM Mono, Syne, #00ff88 accent)
- Deployed at `libro.sequoiaanalytics.com` via Cloudflare Tunnel (same pattern as Signal, AI Librarian)
- No auth required (local network tool)

## Non-goals

- No Instagram scraping in v1 — URL and pasted text only
- No modification of the AI Librarian `books` collection
- No user accounts or multi-user support
- No real-time catalog sync
