# Libro — Hermes Handoff

Read the following spec files in order before doing anything:

1. `01_constitution.md` — what Libro is, constraints, stack
2. `02_specification.md` — full feature spec, LLM client pattern, schema
3. `03_plan.md` — milestones, tasks, requirements, critical implementation notes

Then implement milestone by milestone (M1 → M6), verifying each before proceeding.

## Before you start

- Read `/home/dp/projects/signal/signald/analyzer.py` — copy this LLM client pattern exactly
- Read `/home/dp/projects/ai_librarian/backend/rag.py` — copy the pysqlite3 swap and ChromaDB init pattern exactly
- Read `/home/dp/projects/signal/signal.service` — copy for libro.service
- Read `/home/dp/projects/signal/start.sh` — copy for libro start.sh

Do NOT use the book_scanner at `/home/dp/projects/book_scanner/` — that is a discarded scaffold.

## Key constraints (do not deviate)

- ChromaDB vectorstore lives at `/home/dp/projects/ai_librarian/vectorstore/` — shared, do not create a new one
- `books` collection is READ ONLY — never write to it
- `want_to_read` collection: create if not exists, write all Libro entries here
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`, device=cpu — must match AI Librarian exactly
- LLM fallback chain: OpenCode → Xavier (`192.168.1.110:8080`) → Ollama local (`localhost:11434`)
- Streamlit port: 5252
- No auth gate

## Success criteria

- [ ] `python -c "from libro.store import WantToReadStore; s = WantToReadStore(); print(s.all())"` runs without error
- [ ] `python -c "from libro.librarian import LibrarianIndex; l = LibrarianIndex(); print(l.check_availability('Project Hail Mary', 'Andy Weir'))"` returns a tuple
- [ ] Pasting a book review URL in the UI produces a card with title, author, genre tags, and availability flag
- [ ] Entry persists after page reload
- [ ] `libro.service` starts cleanly with `sudo systemctl start libro`
