from libro.extractor import detect_source_type, fetch_url, clean_text
from libro.analyzer import extract_book
from libro.librarian import LibrarianIndex
from libro.store import WantToReadStore

url = "https://www.cbr.com/best-classic-sci-fi-books-of-all-time-list/"

# Get stores
librarian = LibrarianIndex()
store = WantToReadStore()

# Extract
source_type = detect_source_type(url)
raw_content = fetch_url(url)
cleaned_content = clean_text(raw_content)
book_list = extract_book(cleaned_content, source_type)

print(f"Extracted {len(book_list)} books\n")

# Process like app.py does
any_added = False
for book_data in book_list:
    print(f"Processing: {book_data.get('title')}")
    
    book_data["source_type"] = source_type
    book_data.setdefault("book_type", "")
    book_data.setdefault("source_url", url)
    if not isinstance(book_data.get("genre_tags"), list):
        book_data["genre_tags"] = []
    
    print(f"  Checking availability for {book_data.get('title')}...")
    try:
        available, matched_title = librarian.check_availability(
            book_data["title"], book_data.get("author")
        )
        book_data["available_in_cloud_library"] = available
        book_data["cloud_library_match"] = matched_title
        print(f"    Available: {available}, Match: {matched_title}")
    except Exception as e:
        print(f"    ERROR checking availability: {e}")
        book_data["available_in_cloud_library"] = False
        book_data["cloud_library_match"] = ""
    
    print(f"  Adding to store...")
    try:
        added = store.add(book_data)
        print(f"    Added: {added}")
        if added:
            any_added = True
    except Exception as e:
        print(f"    ERROR adding: {e}")

print(f"\n=== Result ===")
print(f"Any added: {any_added}")
print(f"Total in store: {len(store.all())}")
