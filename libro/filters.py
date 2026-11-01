# Filtering helpers for Libro's want-to-read list.
# Pure functions only, so the tag/filter behaviour can be tested without Streamlit.

import hashlib


def normalize_tag(tag: str) -> str:
    """Canonical form of a tag: trimmed and lowercased.

    ChromaDB stores genre_tags as a comma-joined string, so whitespace and case
    can drift between rows. Normalizing on both write and read keeps tags that
    mean the same thing grouped under one filter button.
    """
    return (tag or "").strip().lower()


def book_tags(book: dict) -> list[str]:
    """Return a book's tags as a de-duplicated list of normalized tags."""
    seen = []
    for raw in book.get("genre_tags") or []:
        tag = normalize_tag(raw)
        if tag and tag not in seen:
            seen.append(tag)
    return seen


def book_id(book: dict) -> str:
    """Stable identifier for a book, matching the id WantToReadStore assigns."""
    return hashlib.md5(f"{book['title']}{book.get('author') or ''}".encode()).hexdigest()


def tag_slug(tag: str) -> str:
    """Short, collision-free suffix for building unique Streamlit widget keys."""
    return hashlib.md5(normalize_tag(tag).encode()).hexdigest()[:8]


def build_tag_index(books: list[dict]) -> list[tuple[str, int]]:
    """Return (tag, book_count) pairs sorted by count desc, then alphabetically.

    The count is the number of *distinct books* carrying the tag, so a book with
    the same tag listed twice only counts once.
    """
    counts: dict[str, set[str]] = {}
    for book in books:
        bid = book_id(book)
        for tag in book_tags(book):
            counts.setdefault(tag, set()).add(bid)
    return sorted(
        ((tag, len(bids)) for tag, bids in counts.items()),
        key=lambda pair: (-pair[1], pair[0]),
    )


def filter_books(
    books: list[dict],
    active_tags: list[str] | None = None,
    query: str = "",
) -> list[dict]:
    """Filter books by selected tags and free-text query.

    Tags are matched exactly (after normalization) and combine with OR: a book
    shows up if it carries *any* of the selected tags. The free-text query is
    matched against the title and summary, and combines with AND against the
    tag selection.
    """
    selected = {normalize_tag(t) for t in (active_tags or [])}
    selected.discard("")
    needle = (query or "").strip().lower()

    results = []
    for book in books:
        if selected and not selected.intersection(book_tags(book)):
            continue
        if needle:
            haystack = f"{book.get('title', '')} {book.get('summary', '')}".lower()
            if needle not in haystack:
                continue
        results.append(book)
    return results
