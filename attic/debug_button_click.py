with open('app.py', 'r') as f:
    content = f.read()

old = '''                    tag_row = st.columns(len(book["genre_tags"]))
                    for idx, tag in enumerate(book["genre_tags"]):
                        if tag_row[idx].button(tag, key=f"tag_{idx}_{book['title']}", use_container_width=True):
                            st.session_state.search_tag = tag
                            st.rerun()'''

new = '''                    tag_row = st.columns(len(book["genre_tags"]))
                    for idx, tag in enumerate(book["genre_tags"]):
                        if tag_row[idx].button(tag, key=f"tag_{idx}_{book['title']}", use_container_width=True):
                            st.toast(f"Clicked: {tag}")
                            st.session_state.search_tag = tag
                            st.rerun()'''

content = content.replace(old, new)

with open('app.py', 'w') as f:
    f.write(content)

print("Added toast debug!")
