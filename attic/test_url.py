from libro.extractor import detect_source_type, fetch_url, clean_text
from libro.analyzer import extract_book

url = "https://collider.com/best-science-fantasy-books-since-2000-ranked/"

print("=== Step 1: Detect source type ===")
source_type = detect_source_type(url)
print(f"Source type: {source_type}")

print("\n=== Step 2: Fetch URL ===")
try:
    raw_content = fetch_url(url)
    print(f"Fetched {len(raw_content)} chars")
    print(f"First 500 chars: {raw_content[:500]}")
except Exception as e:
    print(f"ERROR fetching: {e}")
    exit(1)

print("\n=== Step 3: Clean text ===")
cleaned = clean_text(raw_content)
print(f"Cleaned to {len(cleaned)} chars")
print(f"First 500 chars: {cleaned[:500]}")

print("\n=== Step 4: Extract books ===")
books = extract_book(cleaned, source_type)
print(f"Found {len(books)} books")
for b in books:
    print(f"  - {b.get('title')} by {b.get('author')}")
