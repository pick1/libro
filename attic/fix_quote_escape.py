with open('app.py', 'r') as f:
    content = f.read()

# Fix the quote issue in the key
old = '''                    tag_row = st.columns(len(book["genre_tags"]))
                    for idx, tag in enumerate(book["genre_tags"]):
                        if tag_row[idx].button(tag, key=f"tag_{idx}_{book["title"]}", use_container_width=True):'''

new = '''                    tag_row = st.columns(len(book["genre_tags"]))
                    for idx, tag in enumerate(book["genre_tags"]):
                        if tag_row[idx].button(tag, key=f"tag_{idx}_{book['title']}", use_container_width=True):'''

content = content.replace(old, new)

with open('app.py', 'w') as f:
    f.write(content)

print("Fixed quote escaping!")
