from libro.store import WantToReadStore

store = WantToReadStore()
all_books = store.all()

print(f"Total books in store: {len(all_books)}")
print(f"\nFirst 5 books:")
for i, book in enumerate(all_books[:5]):
    print(f"{i+1}. {book.get('title')} by {book.get('author')}")
    print(f"   Keys: {list(book.keys())}")

# Check for books without titles
no_title = [b for b in all_books if not b.get('title')]
if no_title:
    print(f"\n⚠️  Found {len(no_title)} books with NO TITLE:")
    for b in no_title[:3]:
        print(f"   {b}")
