"""Instagram post/reel text extraction for Libro.

Instagram serves logged-out browsers a JS shell with no post data, but serves
link-preview crawlers a page with the post embedded as JSON plus og: meta tags.
We request as the crawler, then pull this post's caption out of the JSON,
falling back to the meta description.
"""
import json
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

CRAWLER_UA = "facebookexternalhit/1.1"
_SHORTCODE_RE = re.compile(r"/(?:reels?|p|tv)/([A-Za-z0-9_-]+)")


def is_instagram_url(url: str) -> bool:
    host = urlparse(url if "://" in url else f"https://{url}").netloc.lower()
    return host == "instagram.com" or host.endswith(".instagram.com")


def shortcode(url: str) -> str | None:
    m = _SHORTCODE_RE.search(urlparse(url).path)
    return m.group(1) if m else None


def _walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v)


def _from_embedded_json(soup: BeautifulSoup, code: str) -> str:
    # The page embeds several posts (profile grid, related reels), so match on
    # this post's shortcode rather than taking the first caption found.
    for script in soup.find_all("script", type="application/json"):
        raw = script.get_text()
        if code not in raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for node in _walk(data):
            if node.get("code") == code and "caption" in node:
                caption = (node.get("caption") or {}).get("text") or ""
                alt = node.get("accessibility_caption") or ""
                user = (node.get("user") or {}).get("username") or ""
                parts = [
                    f"Instagram post by @{user}" if user else "",
                    caption,
                    f"Image description: {alt}" if alt else "",
                ]
                return "\n".join(p for p in parts if p)
    return ""


def _from_meta(soup: BeautifulSoup) -> str:
    for attr, name in (("property", "og:description"), ("name", "description"),
                       ("property", "og:title")):
        tag = soup.find("meta", attrs={attr: name})
        if tag and tag.get("content"):
            return tag["content"].strip()
    return ""


def fetch_instagram(url: str) -> str:
    if "://" not in url:
        url = f"https://{url}"
    code = shortcode(url)
    if not code:
        raise ValueError(f"Not an Instagram post or reel URL: {url}")

    try:
        resp = requests.get(url, headers={"User-Agent": CRAWLER_UA}, timeout=20)
        resp.raise_for_status()
    except requests.exceptions.Timeout as e:
        raise TimeoutError(f"Timed out fetching {url}") from e
    except requests.exceptions.HTTPError as e:
        raise ValueError(f"HTTP {e.response.status_code} from Instagram") from e
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError(f"Could not reach Instagram: {e}") from e

    soup = BeautifulSoup(resp.text, "html.parser")
    text = _from_embedded_json(soup, code) or _from_meta(soup)
    if not text:
        raise ValueError(f"Instagram returned no data for post {code} (login wall?)")
    return text
