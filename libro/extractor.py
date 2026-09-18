# Web extraction for Libro.
# Fetches and extracts content from URLs or uses raw text.

import re

import requests

from newspaper import Article

from libro.config import CHUNK_SIZE


def fetch_url(url: str) -> str:
    """Fetch URL and extract main article content."""
    # Try trafilatura first - best at stripping boilerplate
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            result = trafilatura.extract(downloaded, include_comments=False, 
                                         include_tables=False, no_fallback=False)
            if result and len(result) > 200:
                return result
    except Exception:
        pass

    # Try newspaper3k
    try:
        from newspaper import Article
        article = Article(url)
        article.download()
        article.parse()
        if article.text and len(article.text) > 200:
            return article.text
    except Exception:
        pass

    # Raw requests fallback
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    resp.raise_for_status()
    return resp.text

def clean_text(text: str) -> str:
    """Strip excess whitespace and truncate to CHUNK_SIZE."""
    # Normalize line endings, collapse multiple blank lines but keep single breaks
    lines = text.splitlines()
    cleaned_lines = []
    prev_blank = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if not prev_blank:
                cleaned_lines.append('')
            prev_blank = True
        else:
            cleaned_lines.append(stripped)
            prev_blank = False
    cleaned = '\n'.join(cleaned_lines).strip()
    if len(cleaned) > CHUNK_SIZE:
        cleaned = cleaned[:CHUNK_SIZE]
    return cleaned

def detect_source_type(input_str: str) -> str:
    """Detect if input is a URL or raw text."""
    if input_str.startswith('http://') or input_str.startswith('https://'):
        return 'url'
    return 'text'
