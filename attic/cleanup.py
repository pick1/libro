with open('app.py', 'r') as f:
    content = f.read()

# Fix 1: Space between genre tags in display
old_tags = '''if book["genre_tags"]:
                    tags_html = "".join([f"<span class='genre-tag'>{tag}</span>" for tag in book["genre_tags"]])'''

new_tags = '''if book["genre_tags"]:
                    tags_html = " ".join([f"<span class='genre-tag'>{tag}</span>" for tag in book["genre_tags"]])'''

content = content.replace(old_tags, new_tags)

# Fix 2: Implement delete by computing book ID
old_delete = '''                if st.button("Delete", key=f"delete_{book['title']}_{book['author'] or 'noauthor'}", help="Remove this book"):
                    # We need to delete by ID, but we don't have the ID here.
                    # We'll need to store the ID in the book data or compute it again.
                    # For now, we'll show a warning that delete is not implemented.
                    st.warning("Delete functionality needs to be implemented by ID.")'''

new_delete = '''                if st.button("Delete", key=f"delete_{book['title']}_{book['author'] or 'noauthor'}", help="Remove this book"):
                    book_id = hashlib.md5(f"{book['title']}{book['author']}".encode()).hexdigest()
                    store.delete(book_id)
                    st.rerun()'''

content = content.replace(old_delete, new_delete)

with open('app.py', 'w') as f:
    f.write(content)

print("Cleaned up!")
