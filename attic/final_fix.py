with open('app.py', 'r') as f:
    content = f.read()

# Replace single book handling with list iteration
old = '''                    # Extract book metadata
                    book_data = extract_book(cleaned_content, source_type)'''

new = '''                    # Extract book metadata (returns a list)
                    book_list = extract_book(cleaned_content, source_type)'''

content = content.replace(old, new)

# Now fix the processing to iterate
old2 = '''                    # Check availability via librarian
                    available, matched_title = librarian.check_availability(
                        book_data["title"], book_data.get("author")
                    )
                    book_data["available_in_cloud_library"] = available
                    book_data["cloud_library_match"] = matched_title
                    
                    # Add to store (deduplication handled inside)
                    added = store.add(book_data)
                    if added:
                        st.success("Book added to your want-to-read list!")
                    else:
                        st.info("This book is already in your list (deduplicated).")
                    
                    # Rerun to update the feed
                    st.rerun()'''

new2 = '''                    # Process each book
                    any_added = False
                    for book_data in book_list:
                        book_data["source_type"] = source_type
                        book_data.setdefault("book_type", "")
                        book_data.setdefault("source_url", "")
                        if isinstance(book_data.get("genre_tags"), str):
                            raw = book_data["genre_tags"]
                            if "," in raw:
                                book_data["genre_tags"] = [t.strip() for t in raw.split(",") if t.strip()]
                            else:
                                book_data["genre_tags"] = [t.strip() for t in raw.split() if t.strip()]
                        elif not isinstance(book_data.get("genre_tags"), list):
                            book_data["genre_tags"] = []
                        
                        if source_type == "url":
                            book_data["source_url"] = user_input
                        
                        # Check availability via librarian
                        available, matched_title = librarian.check_availability(
                            book_data["title"], book_data.get("author")
                        )
                        book_data["available_in_cloud_library"] = available
                        book_data["cloud_library_match"] = matched_title
                        
                        # Add to store
                        added = store.add(book_data)
                        if added:
                            any_added = True
                    
                    if any_added:
                        st.success("Book(s) added to your want-to-read list!")
                    else:
                        st.info("All scanned books are already in your list.")
                    
                    st.rerun()'''

content = content.replace(old2, new2)

with open('app.py', 'w') as f:
    f.write(content)

print("Fixed!")
