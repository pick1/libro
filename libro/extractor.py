import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9",
}

def detect_source_type(text: str) -> str:
    if re.match(r'^https?://', text.strip()):
        return 'url'
    if re.search(r'\w+\.(com|org|net|io|co\.uk|edu|gov)\b', text.strip()):
        return 'url'
    return 'text'

def fetch_url(url: str) -> str:
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        resp.raise_for_status()
        
        if resp.encoding is None:
            resp.encoding = 'utf-8'
        
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')
        
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        
        text = soup.get_text(separator=' ', strip=True)
        
        if len(text) < 20:
            raise ValueError("No content found")
        
        return text
        
    except requests.exceptions.Timeout:
        raise TimeoutError(f"Timeout: {url}")
    except requests.exceptions.HTTPError:
        raise ValueError(f"HTTP error: {url}")
    except Exception as e:
        raise Exception(f"Failed: {str(e)}")

def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'https?://\S+', '[URL]', text)
    return text.strip()
