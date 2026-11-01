import streamlit as st
from libro.store import WantToReadStore

store = WantToReadStore()
all_books = store.all()

st.write(f"Total books: {len(all_books)}")

if all_books:
    st.write("First book data:")
    st.json(all_books[0])
    
    # Try the display logic
    for book in all_books[:2]:
        st.markdown(f"### {book['title']}")
        st.write(f"by {book['author']}")
else:
    st.error("No books in store!")
