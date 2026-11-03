# LLM analysis for Libro.
# Supports OpenRouter (primary), Xavier LAN (fallback), Ollama (local fallback) with book extraction pattern.

import json
import re

import ollama
import requests

from libro.config import (
    OPENROUTER_BASE_URL,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    XAVIER_BASE_URL,
    XAVIER_API_KEY,
    LOCAL_BASE_URL,
    LOCAL_API_KEY,
    LOCAL_MODEL,
)

# Default system prompt for book extraction
BOOK_SYSTEM_PROMPT = """You are an AI assistant that extracts book information from text.
Your goal is to identify all books mentioned in the provided text and return a JSON array of book objects.
Each book object must have the following fields:
- title: string, the title of the book
- author: string, the author of the book (if known, otherwise empty string)
- genre_tags: array of strings, relevant genre tags (e.g., ["sci-fi", "fantasy", "mystery"])
- summary: string, a brief summary of the book (1-2 sentences)
- verdict: string, your overall verdict on the book (e.g., "Highly recommended", "Not worth reading")
- confidence: float between 0.0 and 1.0 indicating your confidence in the extraction

Important rules:
- Return a JSON array, even if only one book is found. Example: [{"title": "Example", ...}]
- If no books are found, return an empty array: []
- Do not include any additional text or explanation outside the JSON array.
- Extract ALL books mentioned in the text, one object per book.
- For list articles (e.g., "Top 10 Cyberpunk Books"), extract each book listed, not the article itself as a book.
- If a field is unknown, use a reasonable default (empty string for title/author, empty array for genre_tags, empty string for summary/verdict, 0.0 for confidence).
- Genre tags should be lowercase and use hyphens for multi-word genres (e.g., "sci-fi", "historical-fiction").
- The summary should be concise and spoiler-free.
- The verdict should be a short phrase expressing your opinion.
- Only extract books (novels, nonfiction, comics, graphic novels). Do not extract TV shows, films, games, music, songs, or podcasts, even if they are discussed.
- Social media captions often credit the background audio with lines like "Earbuds:", "Audio:", "Song:", or "Music:". These are not books; skip them.
- Only extract an item if the text presents it as a book. Do not infer that an unfamiliar title is a book.
- An @handle is not an author name. Use the author's real name if the text gives one or you are confident of it; otherwise leave author empty.
- If you do not recognize a book, keep the summary to what the text says about it and set confidence below 0.5. Never invent plot details.
- Posts often discuss a show, film, or game and then recommend related books. Extract the recommended books; skip the show, film, or game itself.
- Items under a heading like "Book List", "Books", "Recs", or "TBR" are books.
"""

# Set up Ollama client
ollama_client = ollama.Client(host=LOCAL_BASE_URL) if LOCAL_BASE_URL else None

def extract_book(text: str, source_type: str) -> list[dict]:
    """
    Extract book information from text using the LLM with fallback chain.
    Returns a list of book dictionaries.
    """
    # Try providers in order: OpenRouter -> Xavier -> Ollama
    providers = [
        ("openrouter", _call_openrouter),
        ("xavier", _call_xavier),
        ("ollama", _call_ollama),
    ]
    
    for provider_name, provider_func in providers:
        try:
            result = provider_func(text)
            if result:
                return result
        except Exception as e:
            # Log the error and continue to next provider
            print(f"Provider {provider_name} failed: {e}")
            continue
    
    # If all providers fail, return empty list
    return []

def _call_openrouter(text: str) -> list[dict]:
    """Call OpenRouter API."""
    if not OPENROUTER_API_KEY or not OPENROUTER_BASE_URL:
        raise ValueError("OpenRouter API key or base URL not configured")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": BOOK_SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "temperature": 0.1,
        "max_tokens": 2000,
    }
    
    response = requests.post(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    
    content = response.json()["choices"][0]["message"]["content"]
    return _parse_json_result(content)

def _call_xavier(text: str) -> list[dict]:
    """Call Xavier LAN API (OpenAI-compatible)."""
    if not XAVIER_API_KEY or not XAVIER_BASE_URL:
        raise ValueError("Xavier API key or base URL not configured")
    
    headers = {
        "Authorization": f"Bearer {XAVIER_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "local-model",  # Xavier may not care about model name
        "messages": [
            {"role": "system", "content": BOOK_SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "temperature": 0.1,
        "max_tokens": 2000,
    }
    
    response = requests.post(
        f"{XAVIER_BASE_URL}/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    
    content = response.json()["choices"][0]["message"]["content"]
    return _parse_json_result(content)

def _call_ollama(text: str) -> list[dict]:
    """Call Ollama API."""
    if not ollama_client:
        raise ValueError("Ollama client not initialized")
    
    # Ollama expects a prompt, not chat messages. We'll format as a prompt.
    prompt = f"{BOOK_SYSTEM_PROMPT}\n\nExtract book information from the following text:\n\n{text}"
    
    response = ollama_client.generate(
        model=LOCAL_MODEL,
        prompt=prompt,
        format="json",  # Ollama will ensure valid JSON output
        options={
            "temperature": 0.1,
        },
    )
    
    content = response["response"]
    return _parse_json_result(content)

def _parse_json_result(content: str) -> list[dict]:
    """
    Parse the JSON result from the LLM, handling both array and object responses.
    Returns a list of book dictionaries.
    """
    import sys
    pass  # debug print removed
    if not content or not content.strip():
        return []
    
    # Try to find JSON array or object in the content
    # Look for the first '[' or '{' and try to parse from there
    start_idx = content.find('[')
    if start_idx == -1:
        start_idx = content.find('{')
    
    if start_idx == -1:
        # No JSON found
        return []
    
    json_str = content[start_idx:]
    
    try:
        data = json.loads(json_str)
        # If it's a single object, wrap it in a list
        if isinstance(data, dict):
            return [data]
        elif isinstance(data, list):
            return data
        else:
            return []
    except json.JSONDecodeError:
        # If direct parsing fails, try to extract JSON with regex
        # Match the first complete JSON array or object
        json_pattern = r'(\[.*\]|\{.*\})'
        match = re.search(json_pattern, json_str, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                if isinstance(data, dict):
                    return [data]
                elif isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                pass
    
    # If all else fails, return empty list
    return []

def set_notification_callback(callback):
    """Set a callback function for notifications (to be used in the UI)."""
    # This is a placeholder; in a real app we might use it for logging
    pass